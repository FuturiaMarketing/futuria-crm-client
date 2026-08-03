import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

import {
  accountNameFromPayload,
  isValidPrivateKey,
  parseLocationInput,
  startWizard,
  windowsPowerShellEnvironment,
} from "../skills/futuria-crm/scripts/credential-wizard.mjs";

test("estrae l’ID da un link Futuria CRM o da un ID diretto", () => {
  assert.equal(parseLocationInput("demoAccount1234567890"), "demoAccount1234567890");
  assert.equal(
    parseLocationInput("https://app.futuriamarketing.com/v2/location/demoAccount1234567890/dashboard"),
    "demoAccount1234567890",
  );
  assert.equal(
    parseLocationInput("https://app.futuriamarketing.com/location/demoAccount1234567890/settings"),
    "demoAccount1234567890",
  );
});

test("rifiuta host e percorsi non consentiti", () => {
  assert.throws(() => parseLocationInput("https://example.com/v2/location/demoAccount1234567890"));
  assert.throws(() => parseLocationInput("https://app.futuriamarketing.com/settings"));
  assert.throws(() => parseLocationInput("non è un link"));
});

test("valida il formato della chiave privata senza restituirla", () => {
  assert.equal(isValidPrivateKey("pit-preview-key-1234567890"), true);
  assert.equal(isValidPrivateKey("token-preview-key-1234567890"), false);
  assert.equal(isValidPrivateKey("pit-short"), false);
  assert.equal(isValidPrivateKey("pit-invalid value"), false);
});

test("ricava un nome account sicuro dalle forme API note", () => {
  assert.equal(accountNameFromPayload({ location: { name: "Azienda Demo" } }), "Azienda Demo");
  assert.equal(accountNameFromPayload({ company: { name: "Futuria Demo" } }), "Futuria Demo");
  assert.equal(accountNameFromPayload({}), "Account Futuria CRM");
});

test("il server locale usa sessione, cookie e CSRF e completa solo la preview", async (t) => {
  const { server, url } = await startWizard({ preview: true, noOpen: true, port: 0 });
  t.after(() => new Promise((resolve) => server.close(resolve)));

  const pageResponse = await fetch(url);
  assert.equal(pageResponse.status, 200);
  assert.match(pageResponse.headers.get("content-security-policy"), /default-src 'none'/);
  assert.match(pageResponse.headers.get("cache-control"), /no-store/);
  const cookie = pageResponse.headers.get("set-cookie");
  assert.match(cookie, /HttpOnly/);
  assert.match(cookie, /SameSite=Strict/);
  const html = await pageResponse.text();
  assert.match(html, /seleziona <strong>tutti gli ambiti disponibili<\/strong>/);
  assert.match(html, /Gli ambiti lasciati disattivati limiteranno le azioni/);
  const csrf = html.match(/<meta name="csrf-token" content="([a-f0-9]+)">/)?.[1];
  assert.ok(csrf);

  const connectUrl = new URL("connect", url);
  const rejected = await fetch(connectUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: cookie.split(";", 1)[0],
      Origin: "https://example.com",
      "X-Futuria-CSRF": csrf,
    },
    body: JSON.stringify({
      accountLink: "demoAccount1234567890",
      privateKey: "pit-preview-key-1234567890",
    }),
  });
  assert.equal(rejected.status, 403);

  const accepted = await fetch(connectUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: cookie.split(";", 1)[0],
      Origin: new URL(url).origin,
      "X-Futuria-CSRF": csrf,
    },
    body: JSON.stringify({
      accountLink: "https://app.futuriamarketing.com/v2/location/demoAccount1234567890/dashboard",
      privateKey: "pit-preview-key-1234567890",
    }),
  });
  assert.equal(accepted.status, 200);
  const result = await accepted.json();
  assert.deepEqual(result, { ok: true, accountName: "Esempio Azienda", preview: true });
  assert.equal(JSON.stringify(result).includes("pit-preview"), false);
});

test("macOS accetta il salvataggio Keychain dalla pipe senza segreti negli argomenti", {
  skip: process.platform !== "darwin",
}, () => {
  const directory = mkdtempSync(join(tmpdir(), "futuria-keychain-test-"));
  const keychain = join(directory, "test.keychain-db");
  const password = "temporary-keychain-password";
  const service = "com.futuriamarketing.futuria-crm.test";
  const privateKey = "pit-preview-keychain-1234567890";

  try {
    assert.equal(spawnSync("/usr/bin/security", ["create-keychain", "-p", password, keychain]).status, 0);
    assert.equal(spawnSync("/usr/bin/security", ["unlock-keychain", "-p", password, keychain]).status, 0);

    const store = spawnSync("/usr/bin/security", ["-i"], {
      input: `add-generic-password -a default -s ${service} -w ${privateKey} ${keychain}\n`,
      encoding: "utf8",
    });
    assert.equal(store.status, 0, store.stderr);

    const read = spawnSync(
      "/usr/bin/security",
      ["find-generic-password", "-a", "default", "-s", service, "-w", keychain],
      { encoding: "utf8" },
    );
    assert.equal(read.status, 0, read.stderr);
    assert.equal(read.stdout.trim(), privateKey);
  } finally {
    spawnSync("/usr/bin/security", ["delete-keychain", keychain]);
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Windows salva dalla pipe con DPAPI senza esporre la chiave", {
  skip: process.platform !== "win32",
}, () => {
  const directory = mkdtempSync(join(tmpdir(), "futuria-dpapi-test-"));
  const setupScript = join(
    process.cwd(),
    "skills",
    "futuria-crm",
    "scripts",
    "setup-credentials.ps1",
  );
  const environment = windowsPowerShellEnvironment({
    ...process.env,
    APPDATA: directory,
    PSModulePath: "C:\\Program Files\\PowerShell\\Modules",
  });
  assert.equal(
    Object.keys(environment).some((key) => key.toLowerCase() === "psmodulepath"),
    false,
  );

  try {
    const store = spawnSync(
      "powershell.exe",
      ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", setupScript, "-FromStdin"],
      {
        input: "demoAccount1234567890\npit-preview-dpapi-1234567890\n",
        encoding: "utf8",
        env: environment,
      },
    );
    assert.equal(store.status, 0, store.stderr);
    assert.equal(store.stdout.includes("pit-preview"), false);

    const status = spawnSync(
      "powershell.exe",
      ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", setupScript, "-Status"],
      { encoding: "utf8", env: environment },
    );
    assert.equal(status.status, 0, status.stderr);
    assert.match(status.stdout, /Chiave privata protetta: presente/);
    assert.equal(status.stdout.includes("pit-preview"), false);

    const credentialPath = join(directory, "Futuria CRM", "credential.xml");
    const readEnvironment = { ...environment, FUTURIA_TEST_CREDENTIAL_PATH: credentialPath };
    const read = spawnSync(
      "powershell.exe",
      [
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "$c=Import-Clixml -LiteralPath $env:FUTURIA_TEST_CREDENTIAL_PATH; [Console]::Out.Write($c.GetNetworkCredential().Password)",
      ],
      { encoding: "utf8", env: readEnvironment },
    );
    assert.equal(read.status, 0, read.stderr);
    assert.equal(read.stdout, "pit-preview-dpapi-1234567890");

    const config = JSON.parse(readFileSync(join(directory, "Futuria CRM", "config.json"), "utf8"));
    assert.equal(config.location, "demoAccount1234567890");
    assert.equal(config.storage, "windows-dpapi");
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

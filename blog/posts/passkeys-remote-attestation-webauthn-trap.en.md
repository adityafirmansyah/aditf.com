---
title: "The Remote Attestation Trap in Passkeys: Why WebAuthn Threatens User Sovereignty"
slug: passkeys-remote-attestation-webauthn-trap
date: 2026-10-12
excerpt: Passkeys promise phishing-resistant logins, but WebAuthn carries a remote attestation switch. If relying parties turn it on, user-controlled password managers like KeePassXC get locked out.
tags: security, authentication, webauthn, privacy, architecture
---

## The pitch vs the protocol

Big Tech marketed passkeys as the death of passwords. The consumer story sounds simple: public-key cryptography replaces shared secrets, phishing becomes mathematically impossible, and your phone syncs the credentials across your devices.

On the surface, it sounds like an upgrade similar to RFC 6238 TOTP. You get an open standard that any password manager can implement.

The actual W3C WebAuthn Level 3 specification tells a different story.

Deep inside the protocol lies a mechanism called remote attestation. If relying parties choose to mandate it, passkeys stop being exportable user credentials. They turn into non-transferable device certificates that tether your identity to Apple, Google, and Microsoft.

## How remote attestation actually works

When your browser creates a credential via `navigator.credentials.create()`, the server sends a set of options. Most sites today keep the defaults:

```js
const options = {
  publicKey: {
    challenge: new Uint8Array([/* ... */]),
    rp: { name: "Dagango" },
    user: { id: new Uint8Array([/* ... */]), name: "merchant@dagango.com" },
    pubKeyCredParams: [{ alg: -7, type: "public-key" }],
    authenticatorSelection: {
      authenticatorAttachment: "platform",
      userVerification: "required"
    },
    attestation: "direct" // This is the dial.
  }
};
```

That `attestation` parameter is the trapdoor. In consumer applications, it defaults to `"none"`.

When a relying party sets `attestation: "direct"` or `"enterprise"`, the authenticator cannot simply return a new public key. It must return an attestation statement signed by a private key embedded inside the device's secure hardware.

That certificate traces back to a root authority owned by the hardware manufacturer:

- Apple Secure Enclave for iOS and macOS.
- Android StrongBox or Google Titan for Android devices.
- A discrete TPM for Windows machines.

The server does not just verify that you possess the private key. It verifies the exact model of your phone, the integrity of the operating system, and whether the private key was generated inside an unexportable cryptoprocessor.

## Why open-source password managers cannot survive attestation

Here is the collision: software password managers like KeePassXC can easily generate and store passkey credentials. They do the ECDSA or Ed25519 math in memory, save the private key in an encrypted local database, and let you export or sync that database wherever you want.

That exportability is the foundation of user sovereignty. If I want to move my credentials from a Linux desktop to a phone, I copy my vault.

Under strict hardware attestation, that workflow dies.

KeePassXC cannot produce an Apple or Google hardware signature, because KeePassXC is a regular userspace application. It has no hardware root certificate.

If a bank, an airline, or a social network configures its WebAuthn registration endpoint to reject unattested authenticators, your KeePassXC vault fails registration. The server insists on a platform authenticator tied to a sanctioned operating system.

## We already watched this happen on mobile

This is not a theoretical slippery slope. Mobile developers have lived through this exact progression with Google Play Integrity and Apple App Attest.

First, mobile attestation was introduced to stop bots and cheaters in mobile games. Then banking applications adopted it. Today, running a clean Android distribution like LineageOS or GrapheneOS comes with a harsh penalty. Standard banking apps, ride-hailing services, and government portals simply refuse to launch.

The relying party asserts control over your local device. If your client environment does not match their corporate whitelist, you are locked out.

WebAuthn attestation brings that exact DRM architecture to the web browser. For thirty years, the web was defined by client independence: any user agent that spoke HTTP and HTML was a first-class citizen. Attested passkeys flip that model on its head. The server decides whether your browser and password manager are allowed to exist.

## The automation and agent blind spot

Beyond personal privacy, hardware-bound passkeys break automated software.

At Dagango.com, we run automated end-to-end test suites, continuous integration pipelines, and scheduled procurement bots that interact with web interfaces. None of those systems have a human fingerprint scanner or an Apple Secure Enclave attached to the CI runner.

A pure passkey architecture with mandatory hardware attestation makes headless browsers impossible:

- Automated test runners cannot simulate biometric platform gestures without proprietary vendor mocks.
- Background integration workers cannot hold non-transferable hardware keys.
- Autonomous AI agents running on headless Linux servers cannot authenticate to third-party APIs through web flows.

When a service mandates hardware passkeys without a fallback, engineering teams are forced to build fragile backdoor mechanisms: static API keys, bypass flags in staging, or shadow password paths. The "death of passwords" turns into the proliferation of unmonitored service credentials.

## What engineering teams should actually build

Passkeys are genuinely great at preventing credential phishing. The problem is not the cryptography; the problem is using authentication to enforce client certification.

If you are designing authentication for a web platform, follow three rules:

- **Always set `attestation: "none"`.** Never request hardware attestation unless a binding regulatory compliance standard explicitly forces your hand. Accept credentials from any tool the user chooses, including KeePassXC, browser extensions, and standalone vaults.
- **Support cross-platform authenticators.** Do not lock users into `authenticatorAttachment: "platform"`. Allow standalone hardware security keys like YubiKeys alongside platform authenticators.
- **Keep open fallbacks alive.** Provide RFC 6238 TOTP as a supported second factor. TOTP is exportable, offline, scriptable in headless test runners, and entirely client-agnostic.

Passkeys should protect users from attackers on the network. They should never protect platform vendors from users who want to control their own machines.

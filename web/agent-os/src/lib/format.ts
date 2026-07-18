/** Shared number/time formatting — one voice across every panel. */

export const fmtInt = (n: number): string =>
  n.toLocaleString("en-US", { maximumFractionDigits: 0 });

export const fmtTok = (n: number): string =>
  n >= 1e6
    ? `${(n / 1e6).toFixed(2)}M`
    : n >= 1e3
      ? `${(n / 1e3).toFixed(1)}k`
      : fmtInt(n);

export const fmtUsd = (n: number): string =>
  `$${n.toFixed(n >= 10 ? 2 : 4)}`;

export const fmtTime = (iso: string): string =>
  new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

export const fmtDate = (iso: string): string =>
  new Date(iso).toLocaleDateString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

export function fmtMoney(n: number, opts?: { signed?: boolean; compact?: boolean }) {
  const abs = Math.abs(n);
  if (opts?.compact && abs >= 1000) {
    return `${n < 0 ? '-' : opts.signed ? '+' : ''}$${(abs / 1000).toFixed(1)}k`;
  }
  const s = `$${abs.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  if (n < 0) return `-${s}`;
  if (opts?.signed && n > 0) return `+${s}`;
  return s;
}

export function fmtDate(iso: string, opts?: { short?: boolean }) {
  const d = new Date(iso);
  if (opts?.short) {
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

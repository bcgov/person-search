
export function getFormattedDate(format: string = 'YYYY-MM-DD'): string {
    const date = new Date();
    
    const pad = (n: number) => n.toString().padStart(2, '0');
  
    const year = date.getFullYear();
    const month = pad(date.getMonth() + 1); // Months are 0-indexed
    const day = pad(date.getDate());
  
    switch (format) {
      case 'YYYY-MM-DD':
        return `${year}-${month}-${day}`;
      case 'DD/MM/YYYY':
        return `${day}/${month}/${year}`;
      case 'MM-DD-YYYY':
        return `${month}-${day}-${year}`;
      default:
        return `${year}-${month}-${day}`;
    }
  }

  export function getFormattedUTCDate() : string{
  const now = new Date();

  const pad = (num: number, size = 2) => String(num).padStart(size, '0');

  const yyyy = now.getUTCFullYear();
  const mm = pad(now.getUTCMonth() + 1);
  const dd = pad(now.getUTCDate());
  const hh = pad(now.getUTCHours());
  const min = pad(now.getUTCMinutes());
  const ss = pad(now.getUTCSeconds());
  const ms = pad(now.getUTCMilliseconds(), 3);

  return `${yyyy}-${mm}-${dd}T${hh}:${min}:${ss}.${ms}+00:00`;
}
  
export async function request<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api/v1/${path}`, body === undefined ? undefined : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if (!response.ok) throw new Error(`Request failed (${response.status}). Check the API and source status.`);
  return response.json() as Promise<T>;
}
export interface Health {status:string; freshness:string; detail:string|null}
export interface Observation {id:string; phenomenon:string; value:number|string|boolean; unit:string|null; observed_at:string; state:string; quality:string; provenance:{provider:string; source_url:string; quality_note:string|null}}

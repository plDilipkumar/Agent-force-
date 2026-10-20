export async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const token = localStorage.getItem("agentforge_token");
  const headers = new Headers(init.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(input, { ...init, headers });
  if (response.status === 401) {
    localStorage.removeItem("agentforge_token");
    window.dispatchEvent(new Event("agentforge:unauthorized"));
  }
  return response;
}

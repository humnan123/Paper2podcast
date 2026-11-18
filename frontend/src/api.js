const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";


export async function api(
  path,
  {
    method = "GET",
    body = null
  } = {}
) {

  const headers = {};

  // Files (FormData) must NOT get a JSON content type or be stringified.
  const isForm = body instanceof FormData;

  if (!isForm) {
    headers["Content-Type"] = "application/json";
  }


  const token = localStorage.getItem("token");


  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }


  const res = await fetch(
    BASE + path,
    {
      method,
      headers,
      body: body ? (isForm ? body : JSON.stringify(body)) : null,
    }
  );


  const data = await res
    .json()
    .catch(() => ({}));


  if (!res.ok) {
    throw new Error(
      (typeof data.detail === "string" && data.detail) ||
      "Something went wrong"
    );
  }


  return data;
}

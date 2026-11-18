const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";


export async function api(
  path,
  {
    method = "GET",
    body = null
  } = {}
) {

  const headers = {
    "Content-Type": "application/json",
  };


  const token = localStorage.getItem("token");


  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }


  const res = await fetch(
    BASE + path,
    {
      method,
      headers,
      body: body ? JSON.stringify(body) : null,
    }
  );


  const data = await res
    .json()
    .catch(() => ({}));


  if (!res.ok) {
    throw new Error(
      data.detail || "Something went wrong"
    );
  }


  return data;
}
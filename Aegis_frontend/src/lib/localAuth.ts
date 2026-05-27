const USER_ID_KEY = "aegis_user_id";

export function getStoredUserId(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(USER_ID_KEY);
}

export function setStoredUserId(userId: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(USER_ID_KEY, userId);
}

export function clearStoredUserId() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(USER_ID_KEY);
}

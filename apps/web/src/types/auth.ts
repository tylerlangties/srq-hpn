export type UserRole = "admin" | "user";

export type AuthUser = {
  id: number;
  email: string;
  name: string | null;
  role: UserRole;
  is_active: boolean;
};

export type LoginRequest = {
  email: string;
  password: string;
};

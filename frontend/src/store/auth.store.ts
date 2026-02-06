import { makeAutoObservable } from "mobx";

export interface IUser {
  id: number;
  username: string;
  is_admin: boolean;
}

class AuthStore {
  token: string | null = localStorage.getItem("token");
  user: IUser | null = null;

  constructor() {
    makeAutoObservable(this);
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem("token", token);
  }

  setUser(user: IUser) {
    this.user = user;
  }

  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem("token");
  }

  get isLoggedIn() {
    return !!this.token;
  }
}

export const authStore = new AuthStore();

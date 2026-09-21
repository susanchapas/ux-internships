import type { AuthSource, LoginCredentials, RegisterCredentials, User } from './types';

export class ServerAuthSource implements AuthSource {
  private _user: User | null = null;
  private _listeners: Set<(user: User | null) => void> = new Set();
  private _initialized = false;

  get currentUser(): User | null {
    return this._user;
  }

  private _notify() {
    for (const listener of this._listeners) {
      listener(this._user);
    }
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await fetch('/api/me');
      if (response.ok) {
        this._user = (await response.json()) as User;
        this._notify();
        return this._user;
      }
    } catch {
      // Ignore network errors on init
    }
    this._user = null;
    this._notify();
    return null;
  }

  async login(credentials: LoginCredentials): Promise<User> {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Login failed');
    }
    this._user = data as User;
    this._notify();
    return this._user;
  }

  async register(credentials: RegisterCredentials): Promise<User> {
    const response = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Registration failed');
    }
    return data as User;
  }

  async loginWithGoogle(): Promise<User> {
    throw new Error('Google Sign-In is only supported in static mode');
  }

  async logout(): Promise<void> {
    try {
      await fetch('/api/logout', { method: 'POST' });
    } finally {
      this._user = null;
      this._notify();
    }
  }

  onAuthStateChanged(cb: (user: User | null) => void): () => void {
    this._listeners.add(cb);
    if (!this._initialized) {
      this._initialized = true;
      this.getCurrentUser().catch(() => {});
    } else {
      cb(this._user);
    }

    return () => {
      this._listeners.delete(cb);
    };
  }

  async updateUsername(name: string): Promise<void> {
    const response = await fetch('/api/me/username', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: name }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Failed to update username');
    }
    this._user = data as User;
    this._notify();
  }

  async updateEmail(email: string): Promise<void> {
    const response = await fetch('/api/me/email', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Failed to update email');
    }
    this._user = data as User;
    this._notify();
  }

  async updatePassword(current: string, next: string): Promise<void> {
    const response = await fetch('/api/me/password', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password: current, new_password: next }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Failed to update password');
    }
  }
}

export const serverAuthSource = new ServerAuthSource();

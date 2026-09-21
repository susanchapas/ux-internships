import { getApp, getApps, initializeApp } from 'firebase/app';
import {
  EmailAuthProvider,
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  getAuth,
  onAuthStateChanged,
  reauthenticateWithCredential,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateEmail as updateFirebaseEmail,
  updatePassword as updateFirebasePassword,
  updateProfile,
  type User as FirebaseUser,
} from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { ADMIN_EMAIL } from '../utils/constants';
import type { AuthSource, LoginCredentials, RegisterCredentials, User } from './types';

const firebaseConfig = {
  apiKey: 'AIzaSyAC1aXUkAuVGUQNMqczvYR8NJeHbs37HJ8',
  authDomain: 'ux-internships.firebaseapp.com',
  projectId: 'ux-internships',
};

export const firebaseApp = getApps().length ? getApp() : initializeApp(firebaseConfig);
export const firebaseAuth = getAuth(firebaseApp);
export const firestore = getFirestore(firebaseApp);

export function mapFirebaseUser(user: FirebaseUser): User {
  const email = user.email || '';
  const username = user.displayName || email.split('@')[0] || email;
  const role = email === ADMIN_EMAIL ? 'admin' : 'user';

  return {
    id: user.uid,
    username,
    email,
    role,
  };
}

export class FirebaseAuthSource implements AuthSource {
  get currentUser(): User | null {
    const u = firebaseAuth.currentUser;
    return u ? mapFirebaseUser(u) : null;
  }

  async login(credentials: LoginCredentials): Promise<User> {
    const cred = await signInWithEmailAndPassword(
      firebaseAuth,
      credentials.username,
      credentials.password
    );
    return mapFirebaseUser(cred.user);
  }

  async register(credentials: RegisterCredentials): Promise<User> {
    const cred = await createUserWithEmailAndPassword(
      firebaseAuth,
      credentials.email,
      credentials.password
    );
    if (credentials.username) {
      await updateProfile(cred.user, { displayName: credentials.username });
    }
    return mapFirebaseUser(cred.user);
  }

  async loginWithGoogle(): Promise<User> {
    const provider = new GoogleAuthProvider();
    const cred = await signInWithPopup(firebaseAuth, provider);
    return mapFirebaseUser(cred.user);
  }

  async logout(): Promise<void> {
    await signOut(firebaseAuth);
  }

  onAuthStateChanged(cb: (user: User | null) => void): () => void {
    return onAuthStateChanged(firebaseAuth, (user) => {
      cb(user ? mapFirebaseUser(user) : null);
    });
  }

  async getCurrentUser(): Promise<User | null> {
    return this.currentUser;
  }

  async updateUsername(name: string): Promise<void> {
    const user = firebaseAuth.currentUser;
    if (!user) throw new Error('Not authenticated');
    await updateProfile(user, { displayName: name });
  }

  async updateEmail(email: string): Promise<void> {
    const user = firebaseAuth.currentUser;
    if (!user) throw new Error('Not authenticated');
    await updateFirebaseEmail(user, email);
  }

  async updatePassword(current: string, next: string): Promise<void> {
    const user = firebaseAuth.currentUser;
    if (!user || !user.email) throw new Error('Not authenticated');
    const cred = EmailAuthProvider.credential(user.email, current);
    await reauthenticateWithCredential(user, cred);
    await updateFirebasePassword(user, next);
  }
}

export const firebaseAuthSource = new FirebaseAuthSource();

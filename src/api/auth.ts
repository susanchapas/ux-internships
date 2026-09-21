import { firebaseAuthSource } from './auth-firebase';
import { serverAuthSource } from './auth-server';
import { usesFirebaseAuth } from './mode';
import type { AuthSource } from './types';

export type { AuthSource };

export function getAuthSource(): AuthSource {
  return usesFirebaseAuth() ? firebaseAuthSource : serverAuthSource;
}

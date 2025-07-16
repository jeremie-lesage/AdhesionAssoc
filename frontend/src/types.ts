export interface Activity {
  id: number | null;
  name: string;
  description: string;
  location: string;
  max_participants: number;
  current_participants: number;
  is_child_activity: boolean;
  is_adult_activity: boolean;
  resident_price: number | undefined;
  external_price: number | undefined;
}

export interface Adhesion {
  id: number | null;
  code: string;
  email: string;
  nom: string;
  prenom: string;
  numero_rue: string;
  nom_rue: string;
  code_postal: string;
  ville: string;
  adhesion_amount: number;
  activites: string[];
  payment_method?: string;
  status: string;
}

export type AdhesionCreate = Omit<Adhesion, 'id' | 'code' | 'status'>;

export interface AdminUser {
  id: number;
  username: string;
}

export interface AdminUserCreate {
  username: string;
  password?: string;
}

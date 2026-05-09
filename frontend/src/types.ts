export interface Activity {
  id: number | null;
  name: string;
  description: string;
  location: string;
  max_participants: number;
  current_participants: number;
  registration_deadline: string | null;
  day_of_week: number | null;
  start_time: string | null;
  end_time: string | null;
  is_child_activity: boolean;
  is_adult_activity: boolean;
  resident_price: number | undefined;
  external_price: number | undefined;
}

export interface Adhesion {
  id: number | null;
  code: string;
  email: string;
  telephone: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  numero_rue: string;
  nom_rue: string;
  code_postal: string;
  ville: string;
  adhesion_amount: number;
  activities: Activity[];
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

export interface ContactStatus {
  email: string;
  status: string;
  telephone: string | null;
}

export interface FamilyDetails {
  email: string;
  adherents: Adhesion[];
  total_due: number;
}

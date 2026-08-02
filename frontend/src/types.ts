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
  // Nom du PDF à remplir et signer, ou null si l'activité n'en exige aucun.
  // Renseigné par le back-office ; le formulaire s'en sert comme d'un drapeau.
  document_filename: string | null;
}

export interface Adhesion {
  id: number | null;
  code: string;
  email: string;
  telephone: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  nom_rue: string;
  code_postal: string;
  ville: string;
  adhesion_amount: number;
  activities: Activity[];
  payment_method?: string;
  discount_amount: number;
  discount_reason: string | null;
  status: string;
  /** null sur une adhésion validée : l'email de confirmation n'est pas parti. */
  email_sent_at: string | null;
  /** null : l'accusé de réception de la soumission n'est pas parti. */
  submission_email_sent_at: string | null;
}

export type AdhesionCreate = Omit<
  Adhesion,
  'id' | 'code' | 'status' | 'email_sent_at' | 'submission_email_sent_at'
>;

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

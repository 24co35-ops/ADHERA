ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS blood_group text
  CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-') OR blood_group IS NULL);

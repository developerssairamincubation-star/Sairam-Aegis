import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.warn("Missing Supabase frontend environment variables.");
}

export const supabase = createClient(
  supabaseUrl || "http://localhost:54321",
  supabaseKey || "missing-supabase-key",
);

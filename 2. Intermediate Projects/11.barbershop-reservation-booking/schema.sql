-- ==============================================================================
-- Project 11: Barbershop Reservation Booking — Supabase PostgreSQL Schema
-- ==============================================================================

-- 1. Create the Bookings Table
CREATE TABLE IF NOT EXISTS public.bookings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id VARCHAR(64) NOT NULL UNIQUE,
    booking_date DATE NOT NULL,
    time_slot VARCHAR(16) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(64),
    telegram_user_id VARCHAR(64) NOT NULL,
    telegram_username VARCHAR(255),
    service VARCHAR(255) NOT NULL,
    price VARCHAR(32) NOT NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'Confirmed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

-- Ensure column exists if table was already created
ALTER TABLE public.bookings ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(64);

-- 2. Performance Index on Telegram User ID (for instant user security lookups)
CREATE INDEX IF NOT EXISTS idx_bookings_telegram_user_id ON public.bookings (telegram_user_id);

-- 3. Performance Index on Date & Status
CREATE INDEX IF NOT EXISTS idx_bookings_date_status ON public.bookings (booking_date, status);

-- 4. ACID RACE-CONDITION SAFETY: Partial Unique Index
-- Guarantees that only ONE 'Confirmed' booking can exist per date and time slot.
-- Once cancelled, the slot automatically becomes free for other clients!
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_confirmed_slot 
ON public.bookings (booking_date, time_slot) 
WHERE status = 'Confirmed';

-- 5. Enable Row Level Security (RLS) but allow Service Role / Anon access for API
ALTER TABLE public.bookings ENABLE ROW LEVEL SECURITY;

-- Allow read & write access for authenticated service role & anon key
CREATE POLICY "Allow public read-write for booking bot" 
ON public.bookings 
FOR ALL 
USING (true) 
WITH CHECK (true);

-- 6. Insert Sample Test Records
INSERT INTO public.bookings (booking_id, booking_date, time_slot, customer_name, telegram_user_id, telegram_username, service, price, status, notes)
VALUES 
    ('BKG-20261108-1011', '2026-11-08', '10:00', 'John Miller', '987654321', '@johnmiller', 'Classic Haircut & Styling', '€35', 'Confirmed', 'Sample client booking'),
    ('BKG-20261108-1012', '2026-11-08', '14:00', 'Marcus Weber', '876543210', '@mweber', 'The Royal Treatment', '€55', 'Confirmed', 'VIP recurring client')
ON CONFLICT (booking_id) DO NOTHING;


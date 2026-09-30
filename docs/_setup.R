# Shared setup for the paper: load the plotting functions and the APAP results.
Sys.setlocale("LC_TIME", "C")  # English month names whatever the system locale
source("../code/apap_figures.R", chdir = TRUE)
apap <- read_apap("data/apap.sqlite")

weekday <- apap$assignments |> filter(day_type == "weekday")
per_day <- weekday |> count(date, name = "in_order") |>
  left_join(weekday |> filter(shift == "Unassigned") |> count(date, name = "pool"), by = "date")
long_run <- apap$points |> group_by(doctor) |>
  summarise(per_day = sum(total_points) / sum(days_working), days = sum(days_working))

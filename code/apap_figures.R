# APAP figures: peel-off points per doctor over the 2018-2023 schedules.
#
# Reads the compact SQLite snapshot in docs/data/apap.sqlite. Sourced by
# docs/_setup.R; run from docs/ when rendering the paper.
library(DBI)
library(RSQLite)
library(dplyr)
library(tidyr)
library(ggplot2)
theme_set(theme_minimal())

shift_levels <- c("PostCall", "PostHoliday", "PostLate", "PreCall", "PreHoliday",
                  "Unassigned", "OnLate", "OnCall")
role_levels <- c("Cardiac", "Charge", "Both", "Neither")

read_apap <- function(path) {
  con <- dbConnect(SQLite(), path)
  on.exit(dbDisconnect(con))

  doctors <- dbReadTable(con, "doctors") |>
    mutate(across(c(cardiac, charge), as.logical),
           roles = factor(case_when(cardiac & charge ~ "Both", cardiac ~ "Cardiac",
                                    charge ~ "Charge", TRUE ~ "Neither"), levels = role_levels))
  weeks <- dbReadTable(con, "weeks") |>
    mutate(across(c(start, end), as.Date))
  points <- dbReadTable(con, "points") |>
    left_join(weeks |> select(week, start), by = "week") |>
    left_join(doctors |> select(doctor, roles), by = "doctor") |>
    mutate(per_day = total_points / days_working)
  holidays <- dbReadTable(con, "holidays") |>
    mutate(date = as.Date(date))
  assignments <- dbReadTable(con, "assignments") |>
    mutate(date = as.Date(date)) |>
    left_join(holidays, by = "date") |>
    mutate(shift = factor(shift, levels = shift_levels),
           day_type = factor(day_type, levels = c("weekday", "weekend", "holiday")))
  list(doctors = doctors, weeks = weeks, points = points, assignments = assignments,
       holidays = holidays)
}

# Doctors ordered by mean weekly points, so all per-doctor figures share one order.
doctor_order <- function(points) {
  points |> group_by(doctor) |> summarise(m = mean(total_points)) |> arrange(desc(m)) |> pull(doctor)
}

# Weekly points per doctor, raw and per day worked.
plot_weekly_points <- function(points) {
  points |>
    filter(days_working > 0) |>
    mutate(doctor = factor(doctor, levels = doctor_order(points))) |>
    pivot_longer(c(total_points, per_day), names_to = "measure") |>
    mutate(measure = factor(measure, c("total_points", "per_day"),
                            c("Points per week", "Points per day worked"))) |>
    ggplot(aes(doctor, value, fill = roles)) +
    geom_boxplot(outlier.size = 0.6) +
    facet_wrap(~measure, ncol = 1, scales = "free_y") +
    labs(x = NULL, y = NULL, fill = "Qualified for") +
    theme(legend.position = "bottom", axis.text.x = element_text(angle = 90, vjust = 0.5))
}

# Running mean of points per day worked, the quantity the model keeps near the target.
plot_running_mean <- function(points) {
  points |>
    arrange(start) |>
    group_by(doctor) |>
    mutate(running = cumsum(total_points) / cumsum(days_working)) |>
    filter(cumsum(days_working) >= 20) |>  # skip the noisy first weeks of each doctor
    ungroup() |>
    ggplot(aes(start, running, group = doctor)) +
    geom_line(alpha = 0.6, linewidth = 0.4) +
    labs(x = NULL, y = "Cumulative points per day worked")
}

# Weekly target (median points per day worked) and objective components.
plot_objectives <- function(weeks) {
  weeks |>
    pivot_longer(c(target, objective_equity, objective_cardiac_charge, objective_priority_charge),
                 names_to = "component") |>
    mutate(component = factor(component,
      c("target", "objective_equity", "objective_cardiac_charge", "objective_priority_charge"),
      c("Target c (points per day)", "Equity term", "Role spread term", "Charge priority term"))) |>
    ggplot(aes(start, value)) +
    geom_point(size = 0.8, alpha = 0.7) +
    facet_wrap(~component, scales = "free_y") +
    labs(x = NULL, y = NULL)
}

# Days worked per doctor, by day type.
plot_days_worked <- function(assignments, points) {
  lv <- doctor_order(points)
  assignments |>
    count(doctor, day_type) |>
    mutate(doctor = factor(doctor, levels = lv)) |>
    ggplot(aes(doctor, n, fill = day_type)) +
    geom_col() +
    labs(x = NULL, y = "Days worked", fill = NULL) +
    theme(legend.position = "bottom", axis.text.x = element_text(angle = 90, vjust = 0.5))
}

# How often each doctor held each peel-off position on weekdays.
plot_position_heatmap <- function(assignments, points) {
  lv <- doctor_order(points)
  assignments |>
    filter(day_type == "weekday") |>
    count(doctor, points) |>
    group_by(doctor) |>
    mutate(share = n / sum(n)) |>
    ungroup() |>
    mutate(doctor = factor(doctor, levels = lv)) |>
    ggplot(aes(doctor, factor(points), fill = share)) +
    geom_tile(colour = "white") +
    scale_fill_viridis_c(labels = scales::percent) +
    labs(x = NULL, y = "Peel-off position (points)", fill = "Share of\nweekdays") +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5), panel.grid = element_blank())
}

# Points by shift type: fixed shifts have fixed positions, the unassigned pool fills the middle.
plot_shift_points <- function(assignments) {
  assignments |>
    filter(day_type == "weekday") |>
    count(shift, points) |>
    ggplot(aes(factor(points), shift, fill = n)) +
    geom_tile(colour = "white") +
    scale_fill_viridis_c() +
    labs(x = "Peel-off position (points)", y = NULL, fill = "Days") +
    theme(panel.grid = element_blank())
}

# Holiday shifts per doctor.
plot_holidays <- function(assignments, points) {
  lv <- doctor_order(points)
  assignments |>
    filter(!is.na(holiday)) |>
    count(doctor, holiday) |>
    mutate(doctor = factor(doctor, levels = lv)) |>
    ggplot(aes(doctor, holiday, fill = n)) +
    geom_tile(colour = "white") +
    geom_text(aes(label = n), colour = "white", size = 3) +
    scale_fill_viridis_c(end = 0.85) +
    scale_x_discrete(drop = FALSE) +
    labs(x = NULL, y = NULL, fill = "Shifts") +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5), panel.grid = element_blank())
}

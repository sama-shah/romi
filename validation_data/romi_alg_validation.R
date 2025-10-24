# Load necessary libraries
library(dplyr)
library(readr)

# Read the CSV files
hr <- read_csv("resting_heart_rate.csv")
temp <- read_csv("computed_temperature.csv")
self <- read_csv("hormones_and_selfreport.csv")

# Select relevant columns (renaming for consistency)
hr_sel <- hr %>%
  select(
    id,
    study_interval = study_interval,
    is_weekend = is_weekend,
    day_in_study = day_in_study,
    min_heart_rate = value
  )

temp_sel <- temp %>%
  select(
    id,
    study_interval = study_interval,
    is_weekend = is_weekend,
    day_in_study = sleep_end_day_in_study,
    basal_body_temperature = nightly_temperature,
    time_stamp = sleep_end_timestamp
  )

self_sel <- self %>%
  select(
    id,
    study_interval = study_interval,
    is_weekend = is_weekend,
    day_in_study = day_in_study,
    phase
  )

# Convert key columns to matching types for joining
hr_sel <- hr_sel %>%
  mutate(
    is_weekend = as.character(is_weekend),
    day_in_study = as.integer(day_in_study)
  )
temp_sel <- temp_sel %>%
  mutate(
    is_weekend = as.character(is_weekend),
    day_in_study = as.integer(day_in_study)
  )
self_sel <- self_sel %>%
  mutate(
    is_weekend = as.character(is_weekend),
    day_in_study = as.integer(day_in_study)
  )

# Only one temperature entry per participant per day
temp_sel <- temp_sel %>%
  group_by(id, study_interval, is_weekend, day_in_study) %>%
  arrange(time_stamp) %>%
  slice(1) %>%
  ungroup()

# Merge all tables
merged <- hr_sel %>%
  inner_join(temp_sel, by = c("id", "study_interval", "is_weekend", "day_in_study")) %>%
  inner_join(self_sel, by = c("id", "study_interval", "is_weekend", "day_in_study"))

# Create id string e.g., "1_2022"
merged <- merged %>%
  mutate(id = paste(id, study_interval, sep = "_"))

# 2022 (no change in day numbering)
df2022 <- merged %>%
  filter(study_interval == 2022) %>%
  select(
    id,
    study_interval,
    is_weekend,
    day_in_study,
    phase,
    basal_body_temperature,
    time_stamp,
    min_heart_rate
  )

df2024 <- merged %>%
  filter(study_interval == 2024, day_in_study >= 905) %>%
  group_by(id) %>%
  arrange(day_in_study) %>%
  mutate(day_in_study = day_in_study - 904) %>% # renumber days so 905 is 1
  ungroup() %>%
  group_by(id, day_in_study) %>%
  arrange(time_stamp) %>%  # choose the earliest record if multiples per day
  slice(1) %>%
  ungroup() %>%
  select(
    id,
    study_interval,
    is_weekend,
    day_in_study,
    phase,
    basal_body_temperature,
    time_stamp,
    min_heart_rate
  )

# Write to CSV
write_csv(df2022, "mcphases_2022.csv")
write_csv(df2024, "mcphases_2024.csv")

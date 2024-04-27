# Install Libraries
install.packages("tidyverse")

library(tidyverse)
library(dplyr)

# Clean up Alerts data
alert_textfiles <- read_csv("modified_alerts.csv")

doc_name_type <- alert_textfiles %>% 
  mutate(doctor_type = sub(".+\\s(\\S+)$", "\\1", name)) %>% 
  mutate(doctor_type = gsub("\\.", "", doctor_type)) %>% 
  mutate(doc_nameclean = sub(",[^,]*$", "", name)) %>% 
  mutate(doctor_type = case_when(
    str_detect(type, "ithout a License") ~ "Unlicensed",
    str_detect(type, "Cease and Desist") ~ "Unlicensed",
    str_detect(doc_nameclean, doctor_type) ~ NA,
    TRUE ~ doctor_type
  ))

name_cleaning <- doc_name_type %>% 
  separate(doc_nameclean, into = c("first_name", "middle_name", "last_name", "suffix"), sep = "\\s+",
           extra = "merge", fill = "right") %>%
  mutate(
    middle_name = gsub("\\.", "", middle_name),
    middle_name = gsub(",", "", middle_name),
    last_name = gsub(",", "", last_name),
    last_name = gsub("\\.", "", last_name),
    suffix = gsub(",", "", suffix)
  ) %>% 
  mutate(last_name = case_when(
    is.na(last_name) ~ middle_name,
    TRUE ~ last_name
  )) %>% 
  mutate(middle_name = case_when(
    last_name == middle_name ~ NA,
    TRUE ~ middle_name
  )) %>% 
  mutate(clean_name = paste0(first_name, " ", last_name))

doc_typecw <- name_cleaning %>% 
  arrange(doctor_type) %>% 
  distinct(clean_name, .keep_all = TRUE) %>% 
  mutate(doctor_type = case_when(
    str_detect(clean_name, "Poroj|Gig|Shawyer|Wyrick") ~ "Radiographer",
    str_detect(doctor_type, "Therapist") ~ "RT",
    str_detect(doctor_type, "PA") ~ "PA-C",
    TRUE ~ doctor_type
  )) %>% 
  select(clean_name, doctor_type)

doc_typeclean <- name_cleaning %>% 
  select(-doctor_type) %>% 
  left_join(doc_typecw, by ="clean_name")

anti_clean <- doc_typeclean %>%
  select(id, url, clean_name, first_name, middle_name, last_name, suffix, doctor_type, type:date) %>% 
  mutate(license_num = case_when(
    doctor_type == "Unlicensed" ~ NA,
    TRUE ~ substring(id, 1, nchar(id) - 6)
  )) %>% 
  mutate(license_let = str_to_upper(substring(license_num, 1, 1))) %>% 
  mutate(license_dig = as.numeric(gsub("\\D", "", license_num))) %>% 
  mutate(license_dig = case_when(
    is.na(license_dig) ~ NA,
    TRUE ~ sprintf("%07d", license_dig)
    )) %>% 
  mutate(license_num = case_when(
    is.na(license_num) ~ "Unlicensed",
    TRUE ~ paste0(license_let, license_dig)
    )) %>% 
  select(-license_let, -license_dig)
    
write_csv(anti_clean, "clean_nametype.csv")


  

# Install Libraries
install.packages("tidyverse")

library(tidyverse)

# Clean up Alerts data
alert_original <- read_csv("alerts.csv")

clean_license <- alert_original %>% 
  mutate(file_id = case_when(
    str_detect(file_id, "J00031312.239")~"J0003112.239",
    str_detect(file_id, "d1042801.237")~"D1042801.257",
    str_detect(file_id, "d1362907.256")~"D1362907.286",
    str_detect(file_id, "d2792511.096")~"D2792511.146",
    TRUE ~ file_id
  )) %>% 
  mutate(url = paste0("https://www.mbp.state.md.us/BPQAPP/orders/",file_id,".pdf")) %>% 
  mutate(year = substring(year, 1, 4))


write_csv(clean_license, "alerts.csv")

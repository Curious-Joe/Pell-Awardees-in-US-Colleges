setwd("C:/Users/ahfah/Desktop/Data Science Projects/Dash App/pell_students_dash_app/data")

library(readxl)
library(dplyr)
library(httr)

# url_1213 = "https://www2.ed.gov/finaid/prof/resources/data/pell-inst-12-13.xls"
# url_1112 = "https://www2.ed.gov/finaid/prof/resources/data/pell-inst-11-12.xls"
# url_1011 = "https://www2.ed.gov/finaid/prof/resources/data/pell-inst-11-12.xls"
# url_0910 = "https://www2.ed.gov/finaid/prof/resources/data/pell-inst-09-10.xls"

url_1314 = "https://www2.ed.gov/finaid/prof/resources/data/pell-inst-13-14.xls"
url_1415 = "https://www2.ed.gov/finaid/prof/resources/data/pell-inst-14-15.xls"
url_1516 = "https://www2.ed.gov/finaid/prof/resources/data/2015-16distofpellawdsrecipsbyinstn.xlsx"
url_1617 = "https://www2.ed.gov/finaid/prof/resources/data/pellinst1617.xlsx"
url_1718 = "https://www2.ed.gov/finaid/prof/resources/data/pellinst1718.xlsx"

GET(url_1314, write_disk(pell_inst_13_14 <- tempfile(fileext = ".xls")))
year_1314 = read_excel(pell_inst_13_14, col_names = T, skip = 4) %>%
  mutate(Year = "2013-14")

GET(url_1415, write_disk(pell_inst_14_15 <- tempfile(fileext = ".xls")))
year_1415 <- read_excel(pell_inst_14_15, col_names = T, skip = 4) %>%
  mutate(Year = "2014-15")

GET(url_1516, write_disk(pell_inst_15_16 <- tempfile(fileext = ".xlsx")))
year_1516 <- read_excel(pell_inst_15_16, col_names = T, skip = 5) %>%
  mutate(Year = "2015-16")

GET(url_1617, write_disk(pell_inst_16_17 <- tempfile(fileext = ".xlsx")))
year_1617 <- read_excel(pell_inst_16_17, col_names = T, skip = 4) %>%
  mutate(Year = "2016-17")

GET(url_1718, write_disk(pell_inst_17_18 <- tempfile(fileext = ".xlsx")))
year_1718 <- read_excel(pell_inst_17_18, col_names = T, skip = 4) %>%
  mutate(Year = "2017-18")


# rename function ----
rename_cols <- function(dataset, newnames){
  oldNames <- names(dataset)
  
  new <- vector()
  old <- vector()
  
  for(newName in newnames){
    pattern <- strsplit(newName, split = " ")[[1]] %>%
      rlist::list.last()
    oldName <- grep(pattern, oldNames, ignore.case = T, value = T)
    
    new <- append(new, newName)
    old <- append(old, oldName)
  }

    return(
    dataset %>%
      rename_with(~ new[which(old == .x)], .cols = old)
  )
}

newnames <- c(
  "Institution City",
  "Institution Name",
  "Institution State",
  "Institution Type And Control",
  "Ope Id",
  "Total Awards",
  "Total Recipients",
  "Year"
)

# creating final combined data ----
combo <- rename_cols(year_1314, newnames) %>% 
  rbind(rename_cols(year_1415, newnames)) %>% 
  rbind(rename_cols(year_1516, newnames))%>% 
  rbind(rename_cols(year_1617, newnames))%>% 
  rbind(rename_cols(year_1718, newnames)) %>%
  tidyr::drop_na()
write.csv(combo, "pell_grant_data.csv", row.names = F)


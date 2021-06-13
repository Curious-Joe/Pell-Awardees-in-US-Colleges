# ********************************************
# DATA SOURCING AND CLEANING FOR PELL PROJECT ----
# Author: Arafath Hossain
# Date: 06-06-2021
# Description: 
# The US Department of Education stores data on the Pell recipients. 
# The data stored are in excel format in one file per year style with no fixed pattern or format style. 
# This script will serve three purposes: 
# 1. Collect the data from the website,
# 2. Process the data to standardize their format,
# 3. Merge different files to create one single source of data for futher use. 
# ********************************************

# 0.0 PROJECT SET UP ----

# 0.1 Directory ----
setwd("C:/Users/ahfah/Desktop/Data Science Projects/Dash App/pell_students_dash_app")

# 0.1 Loading Libraries ----
library(readxl)
library(rvest)
library(tidyverse)
library(httr)
library(janitor)


# 1.0 DATA SOURCING ----

# 1.1 Web Scraping ----
url <- "https://www2.ed.gov/finaid/prof/resources/data/pell-institution.html"
downloadString <- "https://www2.ed.gov/finaid/prof/resources/data/"

htmlOutput <- read_html(url)

# collect years
years <- htmlOutput %>% 
  html_nodes(".smallindent") %>%
  html_text() %>%
  substr(1, 7)

# collects download link
reportLinks <- htmlOutput %>% 
  html_nodes(".smallindent > a") %>%
  html_attr('href') %>%
  unique()

# year and report match
reportSources <- tibble(
  years = years,
  report_link = paste0(downloadString, reportLinks)
)


# 1.2 Collecting Data ----
downloadData <- function(reportSourcesDF, storageLocation){
    
  df <- tibble()
  
  for(i in seq(1, nrow(reportSourcesDF), 1)){
    reportYear <- reportSourcesDF[i, 1]$years
    report <- reportSourcesDF[i,2] 
    fileExt <- tools::file_ext(report)
    outputLocation <- paste0(storageLocation, reportYear, ".csv")
    
    # downloads and save file temporarily
    GET(report$report_link, write_disk(
      yearlyReport <- tempfile(fileext = fileExt))
    )
    # removes introductory paragraphs from the excel files
    yearlyReport = read_excel(yearlyReport, col_names = F)
    yearlyReport <- yearlyReport[!is.na(yearlyReport[,1]), ]
    yearlyReport <- yearlyReport[!is.na(yearlyReport[,2]), ]
    yearlyReport <- yearlyReport[!is.na(yearlyReport[,3]), ]
    
    # promotes first full row as column names
    yearlyReport <- yearlyReport %>%
      janitor::row_to_names(row_number = 1)
    
    # writes back to the desired location
    yearlyReport %>%
      write_excel_csv(outputLocation)
    
    # populates a summary report with col names 
    cols <- as_tibble(names(yearlyReport))
    cols$year <- reportYear
    df <- rbind(df, cols)
  }
  
  return(df)
}

reportSourcesSummary <- downloadData(reportSources, "data/")

# 1.3 Data Cleaning ----
# Convert char data type to factor
str(reportSourcesSummary)
reportSourcesSummary <- reportSourcesSummary %>%
  mutate_if(is.character, as.factor)
summary(reportSourcesSummary)

unique(reportSourcesSummary$year) %>% length()
table(reportSourcesSummary$value) %>% sort(decreasing = T)

# Convert values to upper case
reportSourcesSummary$valueCln <- toupper(reportSourcesSummary$value)
table(reportSourcesSummary$value) %>% sort(decreasing = T)

# Unify similar name
similarColCount <- function(df, targetCol, keyword){

  cols <- unique(
    grep(keyword, pull(df, {{targetCol}}), ignore.case = T, value = T)
)
  filter(df, {{targetCol}} %in% c(cols)) %>%
    count({{targetCol}}, sort = T) 
  
}

similarColCount(reportSourcesSummary, valueCln, "awards")
similarColCount(reportSourcesSummary, valueCln, "city")



# Total cols in each report
reportSourcesSummary %>%
  ggplot(aes(y = year)) +
  geom_bar(stat = "count", width = .5, show.legend = F, fill = "grey") +
  labs(
    y = "Year", x = "Total", title = "Year wise total columns"
  ) + 
  theme_minimal()

# Report with exact same columns
table(reportSourcesSummary)
  


# 2.0 DATA PREPARATION ----
# 2.1 Function for Data Processing ----
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

  print(paste0("Old col namess:", (paste0(old, collapse = ", "))))
  print(paste0("New col namess:", (paste0(new, collapse = ", "))))    
  
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

# 2.2 Data Process, Aggregating, and Storing ----
combo <- rename_cols(year_1314, newnames) %>% 
  rbind(rename_cols(year_1415, newnames)) %>% 
  rbind(rename_cols(year_1516, newnames))%>% 
  rbind(rename_cols(year_1617, newnames))%>% 
  rbind(rename_cols(year_1718, newnames)) %>%
  tidyr::drop_na()
write.csv(combo, "pell_grant_data.csv", row.names = F)


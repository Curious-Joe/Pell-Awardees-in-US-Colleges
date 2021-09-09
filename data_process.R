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
library(patchwork)


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

# 1.3 Data Explore ----

# Total columns difference 
yearly_cols <- reportSourcesSummary %>%
  ggplot(aes(y = year)) +
  geom_bar(stat = "count", width = .5, show.legend = F, color = "#4a0202") +
  labs(
    y = "Year", x = "Total", 
    title = "Varying Column Counts for the Same Report Over the Years"
  ) +
  fastEda::theme_fasteda(color = "#0a0a0a") +
  theme(plot.title = element_text(size = 12))


# Non standardized column names
similarColCount <- function(df, targetCol, keyword){
  
  cols <- unique(
    grep(keyword, pull(df, {{targetCol}}), ignore.case = T, value = T)
  )
  filter(df, {{targetCol}} %in% c(cols)) %>%
    count({{targetCol}}, sort = T) 
  
}

uns_col_names <-
  similarColCount(reportSourcesSummary, value, "name") %>%
  mutate(info_type = "Institution Name Cols") %>%
  rbind(
    similarColCount(reportSourcesSummary, value, "awards") %>%
      mutate(info_type = "Award Amount Cols")
  ) %>%
  rbind(
    similarColCount(reportSourcesSummary, value, "city") %>%
      mutate(info_type = "City Name Cols")
  ) %>%
ggplot(
  aes(y = reorder(value, n), x = n, color = "#4a0202")
) + 
  geom_col(show.legend = F) +
  facet_grid(info_type ~ ., scales = "free", space = "free") + 
  labs(
    title = "Varying Column Names Reporting Same Data",
    y = NULL,
    x = "Total"
  ) +
  fastEda::theme_fasteda(color = "#0a0a0a") +
  theme(panel.border = element_rect(color = "white", fill = NA, size = 1)) +
  theme(strip.background =element_rect(fill="black"))+
  theme(strip.text = element_text(colour = 'white')) +
  theme(plot.title = element_text(size = 12))

# Combining data vizes
yearly_cols + uns_col_names +
  plot_annotation(
    title = "A Brief Data Nightmare: Inconsistent Data Reporting",
    subtitle = "Data Inconsistencies in the Web Scrapped Pell Grant Data",
    caption = "Prepared By: Arafath Hossain \n #dash_app_pell",
    theme = fastEda::theme_fasteda(color = "#e6e6e6") +
      theme(text = element_text(color = "black"),
            plot.title = element_text(size = 14, hjust = 0.5),
            plot.subtitle = element_text(size = 10, hjust = 0.5, vjust = 5))
  ) 

# 1.4 Data Cleaning ----
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

# Report with exact same columns
table(reportSourcesSummary)
  


# 2.0 DATA PREPARATION ----
# 2.1 Function for Data Processing ----
rename_cols <- function(dataset, nameMatchDf, matchOldCol, matchNewCol){
  
  # setting up variables
  oldNames <- names(dataset)
  newNames <- unique(nameMatchDf %>% pull({{matchNewCol}}))
  newNamesCopy <- newNames
  name_match <- tibble(old = as.character(), new = as.character()) # blank tibble to store old and new name match pairs
  
  # iterating over the dataset to find old and new name match
  for(matchOldName in pull(nameMatchDf, {{matchOldCol}})){
    pattern <- strsplit(matchOldName, split = " ")[[1]] %>%
      rlist::list.last()
    oldName <- grep(pattern, oldNames, ignore.case = T, value = T)
    
    if(rlang::is_empty(oldName)){
      message(paste0(matchOldName, " doesn't exist!"))
    } else {
      if(length(oldName) > 1){
        message(glue::glue("{pattern} matches multiple cols!"))
      }else {
        newName <- filter(nameMatchDf, {{matchOldCol}} == oldName) %>%
          pull({{matchNewCol}})
        # newName <- grep(oldName, 
        #                 pull(nameMatchDf, {{matchNewCol}}), 
        #                 ignore.case = T, 
        #                 value = T) %>% 
        #   unique()
        print(glue::glue("new name: {newName}"))
      }
      
      # checking if new column is already detected and skipped if already populated
      if(sum(oldNames %in% matchOldName) == 1) {
        name_match <- name_match %>%
          bind_rows(c(old = matchOldName, new = newName)) %>%
          unique() %>%
          drop_na() # drops name matches where no matched old column exists
        print(glue::glue("new names: {name_match$new}"))
        print(glue::glue("old names: {name_match$old}"))
        newNames <- newNames[!newNames %in% newName]
      }
    }
  }
  # print(glue::glue("new names: {name_match$new}"))
  # print(glue::glue("old names: {name_match$old}"))
  # keeping only the columns that match with new names
  dataset <- select({dataset}, all_of(name_match$old))
  # print(glue::glue("old names: {names(dataset)}"))
  # renaming old column names
  colnames(dataset) <- name_match$new
  
  # adding null for the absent columns
  absentCols <- setdiff(newNamesCopy, names(dataset))
  for(col in absentCols){
    print(paste0("Absent col: ", col))
    dataset <- dataset %>%
      mutate(!!col := NA)
  }
  
  return(dataset)
}

# setting up a table with old names and new names matches
name_match_df <- tibble(
  oldNames = c(
    "Name", "Institution", "Institution_Name",
    "Institution City", "City", "Institution_City",
    "Institution State", "State", "Institution_State",
    "Total Awards", "Awards", "Total_Awards", 
    "Total Recipients", "Recipients", "Total_Recipients",
    "Year"
    
  ),
  
  newNames = c(
    "Institution Name", "Institution Name", "Institution Name",
    "Institution City", "Institution City", "Institution City",
    "Institution State", "Institution State", "Institution State",
    "Total Awards", "Total Awards", "Total Awards",
    "Total Recipients", "Total Recipients", "Total Recipients",
    "Year"
  )
)
name_match_df$oldNames <- toupper(name_match_df$oldNames)

# loading all files
files <- list.files("data/")
data_combo <- NULL
for(file in files){
  
  year = strsplit(file, ".csv")[[1]]
  data <- read.csv(paste0("data/", file)) %>%
    mutate(Year = year)
  names(data) <- toupper(names(data))
  message(glue::glue("\n Processing file for: {year}"))
  data <- rename_cols(
    dataset = data, 
    nameMatchDf = name_match_df,
    matchOldCol = oldNames, 
    matchNewCol = newNames)
  
  data_combo <<- data_combo %>%
    rbind(data)
}

# creating column for year start and session
data_combo <- data_combo %>%
  rename(Session = Year) %>%
  separate(Session, sep = "-", into = c("Year", NA), remove = F) 

write.csv(data_combo, "data/pell_grant_data.csv", row.names = F)


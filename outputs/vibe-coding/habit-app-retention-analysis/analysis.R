#missing data 삭제
# 필요한 패키지 불러오기
library(dplyr)
library(ggplot2)
library(lubridate)

# 데이터 불러오기
app_log <- read.csv("MR_data.csv")

# 결측치 제거 (선택 사항)
app_log <- na.omit(app_log)

# 날짜 형식 변환 (컬럼명: date)
app_log$date <- as.Date(app_log$date)

# 사용자별 첫 사용일과 마지막 사용일 추출
user_periods <- app_log %>%
  group_by(user_id) %>%
  summarise(start_date = min(date),
            end_date = max(date)) %>%
  arrange(start_date)

# 사용자에 보기 쉬운 라벨 붙이기
user_labels <- user_periods %>%
  distinct(user_id) %>%
  mutate(user_label = paste0("User ", row_number()))

# 라벨 병합
user_periods_labeled <- user_periods %>%
  left_join(user_labels, by = "user_id")

# 라벨 순서 고정 (정렬을 위해 factor 지정)
user_periods_labeled$user_label <- factor(user_periods_labeled$user_label,
                                          levels = user_periods_labeled$user_label)

# 수평 막대그래프 그리기
ggplot(user_periods_labeled, aes(y = user_label)) +
  geom_segment(aes(x = start_date, xend = end_date, yend = user_label),
               size = 2, color = "steelblue") +
  labs(title = "사용자별 앱 사용 기간",
       x = "날짜", y = "사용자") +
  theme_minimal()

library(openxlsx) 
library(dplyr)
library(lubridate)
library(tidyr)


df=read.csv('MR_data.csv')

  #앱 필터링
  filter_app<-c("todolist.scheduleplanner.dailyplanner.todo.reminders",
                "kr.gseek.mobile.app",
                "kr.go.seoul.healthcare",
                "kr.co.whitecube.chlngers",
                "com.YBMSisa",
                "com.sec.android.app.shealth",
                "com.rirosoft.riroschool",
                "com.mih.planfit",
                "com.inbody2014.inbody",
                "com.hanbit.rundayfree",
                "com.hackers.app.hackersmp3",
                "com.google.android.apps.healthdata",
                "com.google.android.apps.fitness",
                "com.fitbit.FitbitMobile",
                "com.dencreak.weightwar",
                "com.cocoswing.tedict",
                "com.facebook.katana", "com.instagram.android", "com.twitter.android" , "com.kakao.talk" , "com.nhn.android.search")
df <- df %>% 
  filter(app_name %in% filter_app)


  #1월25일이후 기록이 있는 사람들만 남기기
  df$date <- as.Date(df$date)
cutoff_date <- as.Date("2025-01-25")

# 1월 25일 이후 기록이 있는 user_id 추출
active_users <- unique(df$user_id[df$date >= cutoff_date])

# 이 user_id만 남기고 나머지는 제거
df <- df[df$user_id %in% active_users, ]

  #12월1일부터 데이터 존재해야함
  users_dec1 <- unique(df$user_id[df$date == as.Date("2024-12-01")])
df <- df[df$user_id %in%users_dec1, ]

  #이상치 제거
  Q1 <- quantile(df$total_time, 0.25, na.rm = TRUE)
Q3 <- quantile(df$total_time, 0.75, na.rm = TRUE)
IQR_value <- Q3 - Q1

# 이상치 기준 계산 (1.5 * IQR)
lower_bound <- Q1 - 1.5 * IQR_value
upper_bound <- Q3 + 1.5 * IQR_value

# 이상치가 아닌 데이터만 남기기
df <- df %>%
  filter(total_time >= lower_bound & total_time <= upper_bound)

  #유저 라벨링
  
  unique_users <- unique(df$user_id)
user_labels <- paste0("user_", match(df$user_id, unique_users))

# 새로운 열에 라벨 할당
df$user_label <- user_labels

  #주차 적기
 
start_date <- min(df$date)
start_year <- year(start_date)

# 12월 첫째주를 찾기 (해당 연도의 12월 1일이 속한 주의 월요일)
dec_first <- as.Date(paste0(start_year, "-12-01"))
dec_first_week_start <- dec_first - wday(dec_first) + 2  # 월요일

# 만약 데이터가 여러 해에 걸쳐 있다면, 가장 이른 12월 1일 기준으로 잡음
all_dec_first <- as.Date(paste0(unique(year(df$date)), "-12-01"))
all_dec_first_week_start <- min(all_dec_first - wday(all_dec_first) + 2)

# 기준일(12월 첫째주 월요일)부터 몇 주가 지났는지 계산
df <- df %>%
  mutate(custom_week = as.integer(difftime(date, all_dec_first_week_start, units = "weeks")) + 1)

  # 작심삼일 앱 사용 여부 구하기 (앞서 제공한 코드와 동일)
  jaksim_apps <- c( "todolist.scheduleplanner.dailyplanner.todo.reminders",
                    "kr.gseek.mobile.app", "kr.go.seoul.healthcare",
                    "kr.co.whitecube.chlngers","com.YBMSisa",
                    "com.sec.android.app.shealth",
                    "com.rirosoft.riroschool",  "com.mih.planfit",
                    "com.inbody2014.inbody",  "com.hanbit.rundayfree",
                    "com.hackers.app.hackersmp3","com.google.android.apps.healthdata",
                    "com.google.android.apps.fitness",
                    "com.fitbit.FitbitMobile","com.dencreak.weightwar", "com.cocoswing.tedict")

user_jaksim <- df %>%
  filter(app_name %in% jaksim_apps) %>%
  distinct(user_id) %>%
  mutate(jaksim_user = "yes")

user_list <- df %>%
  distinct(user_id)
user_list <- user_list %>%
  left_join(user_jaksim, by = "user_id") %>%
  mutate(jaksim_user = ifelse(is.na(jaksim_user), "no", jaksim_user))

df <- df %>%
  left_join(user_list, by = "user_id")

 #주말여부
  weekday_num <- as.POSIXlt(df$date)$wday
df$is_weekend <- ifelse(weekday_num %in% c(0, 6), 1, 0)

  #카테고리
  df$category <- with(df, ifelse(app_name %in% c("todolist.scheduleplanner.dailyplanner.todo.reminders"),
                                 "productivity",
                                 ifelse(app_name %in% c("kr.go.seoul.healthcare",
                                                        "kr.co.whitecube.chlngers",
                                                        "homeworkout.fitness.app",
                                                        "com.sec.android.app.shealth",
                                                        "com.mih.planfit",
                                                        "com.inbody2014.inbody",
                                                        "com.hanbit.rundayfree",
                                                        "com.google.android.apps.healthdata",
                                                        "com.google.android.apps.fitness",
                                                        "com.fitbit.FitbitMobile",
                                                        "com.dencreak.weightwar"),
                                        "health",
                                        ifelse(app_name %in% c("kr.gseek.mobile.app",
                                                               "com.YBMSisa",
                                                               "com.rirosoft.riroschool",
                                                               "com.hackers.app.hackersmp3",
                                                               "com.cocoswing.tedict"),
                                               "education",
                                               ifelse(app_name %in% c("com.facebook.katana", 
                                                                      "com.instagram.android", 
                                                                      "com.twitter.android"),
                                                      "SNS",
                                                      ifelse(app_name %in% c("com.kakao.talk", 
                                                                             "com.nhn.android.search"),
                                                             "daily",
                                                             "other"))))))

  #sns한번이라도 사용한 사람

used_sns_users <- unique(df$user_id[df$category %in% "SNS"])

# 새로운 변수 추가: 1(한번이라도 사용), 0(한번도 사용 X)
df$used_sns_apps <- ifelse(df$user_id %in% used_sns_users, 1, 0)

  #작심삼일앱인지 여부
  df$is_jaksim <- ifelse(df$category %in% c("productivity", "health", "education"), 1, 0)

  #0처리
  
  # 1. 유저별 실제 사용한 앱 추출
  user_app_pairs <- df %>%
    distinct(user_id, app_name)
  
  # 2. 전체 날짜 범위 생성
  full_dates <- seq(as.Date("2024-12-01"), as.Date("2025-01-31"), by = "day")
  
  # 3. user_id × app_name × date 조합 생성
  full_user_app_date <- user_app_pairs %>%
    crossing(date = full_dates)
  
  # 4. 기존 데이터와 병합
  df_filled <- full_user_app_date %>%
    left_join(df, by = c("user_id", "app_name", "date"))
  
  # 5. 사용하지 않은 날짜는 total_time = 0으로
  df_filled <- df_filled %>%
    mutate(total_time = ifelse(is.na(total_time), 0, total_time))
  
  # 6. 부가 변수 보완 (user_id 단위 + app_name 단위 기준)
  df_filled <- df_filled %>%
    group_by(user_id) %>%
    fill(age, user_label, jaksim_user, is_weekend, custom_week, used_sns_apps, .direction = "downup") %>%
    ungroup() %>%
    group_by(app_name) %>%
    fill(category, .direction = "downup") %>%
    ungroup()
  
  # 7. 작심삼일 앱 플래그 다시 계산 (category 기준)
  df_filled <- df_filled %>%
    mutate(is_jaksim = ifelse(category %in% c("productivity", "education", "health"), 1, 0))
  
  # 8. 정렬
  df_filled <- df_filled %>%
    arrange(user_id, app_name, date)
  
  # custom_week 다시 계산: 12월 1일부터 7일 단위로 주차 설정
  df_filled <- df_filled %>%
    mutate(custom_week = as.integer((as.Date(date) - as.Date("2024-12-01")) / 7) + 1)
  
  df_filled <- df_filled %>%
    mutate(
      date = as.Date(date),  # 안전하게 형 변환
      weekday_num = wday(date, week_start = 1),  # 월요일=1, 일요일=7
      is_weekend = ifelse(weekday_num %in% c(6, 7), 1, 0)
    ) %>%
    select(-weekday_num)  # 필요 없으면 삭제
  
  # 탐색적 분석 1
  library(dplyr)
  library(lubridate)
  library(ggplot2)
  
  # 날짜 형식 변환 및 종료일 정의
  df_filled$date <- as.Date(df_filled$date)
  end_date <- max(df_filled$date)
  
  # 작심삼일 조건 함수 정의 (total_time > 0 기준)
  check_jaksim <- function(data) {
    used_dates <- sort(unique(data$date[data$total_time > 0]))
    
    # 조건 1: 전체 기간 중 7일 이내 3일 이상 사용한 구간 존재
    cond1 <- FALSE
    if (length(used_dates) >= 3) {
      for (i in 1:(length(used_dates) - 2)) {
        win_start <- used_dates[i]
        win_end <- win_start + 6
        within_window <- used_dates[used_dates >= win_start & used_dates <= win_end]
        if (length(within_window) >= 3) {
          cond1 <- TRUE
          break
        }
      }
    }
    
    # 조건 2: 마지막 사용 이후로 다시 사용 기록 없음
    if (length(used_dates) == 0) return(FALSE)
    last_use <- max(used_dates)
    if (last_use >= end_date) return(FALSE)
    after_last <- seq(last_use + 1, end_date, by = "day")
    cond2 <- all(!(after_last %in% used_dates))
    
    return(cond1 & cond2)
  }
  
  # 사용자-앱 단위로 작심삼일 여부 계산
  result <- df_filled %>%
    arrange(user_id, app_name, date) %>%
    group_by(user_id, app_name, age) %>%
    summarise(is_jaksim = check_jaksim(cur_data()), .groups = "drop")
  
  #  작심삼일 조건 만족 + 카테고리 필터링 (education, health, productivity)
  jaksim_filtered <- result %>%
    filter(is_jaksim == TRUE) %>%
    inner_join(df_filled %>%
                 filter(category %in% c("education", "health", "productivity")) %>%
                 select(user_id, app_name) %>% distinct(),
               by = c("user_id", "app_name"))
  
  # 시각화용 데이터 생성
  plot_df <- df_filled %>%
    filter(category %in% c("education", "health", "productivity")) %>%
    semi_join(jaksim_filtered, by = c("user_id", "app_name")) %>%
    mutate(label = paste0(user_id, "\n", app_name, " (", age, ")"))
  
  # 사용자-앱 시각화 (facet_wrap)
  ggplot(plot_df, aes(x = as.Date(date), y = total_time)) +
    geom_line(color = "steelblue") +
    geom_point(color = "red", size = 1) +
    facet_wrap(~ label, scales = "free_y", ncol = 4) +
    labs(
      title = "작심삼일 사용자-앱 사용 패턴 (교육/건강/생산성)",
      x = "날짜", y = "총 사용 시간 (초)"
    ) +
    theme_minimal(base_size = 10) +
    theme(strip.text = element_text(size = 8))
  
  
  #탐색적 분석2
  
  #유저별 주차별 total_time합
  result <- df_filled%>%
    group_by(user_id, custom_week, jaksim_user,is_jaksim) %>%
    summarise(total_time = sum(total_time, na.rm = TRUE), .groups = "drop")
  
  result_avg <- result %>%
    group_by(jaksim_user, is_jaksim, custom_week) %>%
    summarise(mean_total_time = mean(total_time, na.rm = TRUE), .groups = "drop")
  
  # 그룹명을 한 컬럼으로 합치기 (예: yes_1, no_0 등)
  result_avg <- result_avg %>%
    unite("group", jaksim_user, is_jaksim, sep = "_")
  
  # 피벗 테이블 생성: group별로 행, custom_week별로 열
  pivot_table <- result_avg %>%
    pivot_wider(names_from = custom_week, values_from = mean_total_time)
  
  
  
  
  library(ggplot2)
  
  
  # group 컬럼을 다시 분리해서 사용여부/앱여부로 나누기 (그래프 범례용)
  result_avg <- result_avg %>%
    separate(group, into = c("jaksim_user", "is_jaksim"), sep = "_") %>%
    mutate(
      jaksim_user = ifelse(jaksim_user == "yes", "작심삼일 앱 사용자", "미사용자"),
      is_jaksim = ifelse(is_jaksim == "1", "작심삼일 앱", "비작심삼일 앱")
    )
  
  # 선그래프 그리기
  ggplot(result_avg, aes(x = custom_week, y = mean_total_time, 
                         color = jaksim_user, linetype = is_jaksim, group = interaction(jaksim_user, is_jaksim))) +
    geom_line(size = 1) +
    geom_point(size = 2) +
    labs(
      title = "주차별 평균 total_time (작심삼일 앱 사용여부/앱여부별)",
      x = "주차(custom_week)",
      y = "평균 total_time",
      color = "작심삼일 앱 사용여부",
      linetype = "앱 종류"
    ) +
    theme_minimal()
  
  #작심삼일앱만 따로 보기 
  result_avg_jaksim <- result_avg %>%
    filter(is_jaksim == "작심삼일 앱")
  
  ggplot(result_avg_jaksim, aes(x = custom_week, y = mean_total_time, 
                                color = jaksim_user, group = jaksim_user)) +
    geom_line(size = 1) +
    geom_point(size = 2) +
    scale_x_continuous(breaks = 1:9) +
    labs(
      title = "주차별 평균 total_time (작심삼일 앱만, 사용여부별)",
      x = "주차(custom_week)",
      y = "평균 total_time",
      color = "작심삼일 앱 사용여부"
    ) +
    theme_minimal()
  
  
  #탐색적분석3
  
  #sns사용여부별
  df_jaksim <- df_filled %>% filter(is_jaksim %in% "1")
  
  # 유저별, custom_week별 total_time 합계 집계
  result_sns <- df_jaksim %>%
    group_by(user_id, custom_week, used_sns_apps) %>%
    summarise(total_time = sum(total_time, na.rm = TRUE), .groups = "drop")
  result_avg_sns <- result_sns %>%
    group_by(used_sns_apps, custom_week) %>%
    summarise(mean_total_time = mean(total_time, na.rm = TRUE), .groups = "drop")
  
  #  시각화
  library(ggplot2)
  result_avg_sns$used_sns_apps <- factor(result_avg_sns$used_sns_apps, levels = c(1,0), labels = c("SNS 사용", "SNS 미사용"))
  ggplot(result_avg_sns, aes(x = custom_week, y = mean_total_time, color = used_sns_apps, group = used_sns_apps)) +
    geom_line(size = 1) +
    geom_point(size = 2) +
    scale_x_continuous(breaks = 1:9) +
    labs(
      title = "주차별 평균 total_time (SNS 사용여부별)",
      x = "주차(custom_week)",
      y = "평균 total_time",
      color = "SNS 사용여부"
    ) +
    theme_minimal()
  
  #회귀분석:가설1
  
  # 1. 작심삼일앱만 필터링 (is_jaksim == 1)
  df_jaksim <- df_filled %>% filter(is_jaksim == 1)
  
  
  # 2. 유저별·날짜별 그룹화 및 집계
  df_jaksim_group <- df_jaksim %>%
    group_by(user_id, date) %>%
    summarise(
      total_time = sum(total_time, na.rm = TRUE),
      is_weekend = first(is_weekend),
      age = first(age),
      num_health_apps = sum(category == "health" & total_time > 0),
      num_apps = n_distinct(app_name[total_time > 0])
    ) %>%
    mutate(
      health_app_ratio = ifelse(num_apps == 0, 0, num_health_apps / num_apps)
    )
  
  
  
  df_jaksim_group$date_num <- as.numeric(as.Date(df_jaksim_group$date))
  df_jaksim_group$date_num2 <- df_jaksim_group$date_num^2
  
  model_quad <- lm(
    total_time ~ date_num + date_num2 + num_apps + health_app_ratio + age + is_weekend,
    data = df_jaksim_group)
  
  summary(model_quad)
  
  #회귀분석_가설2
  #이탈 함수 생성
  
  # 패키지 로딩
  library(ggplot2)
  library(lubridate)
  #작심삼일카테고리한정
  df_filled <- df_filled %>%
    filter(category %in% c("health", "education", "productivity"))
  # 날짜 변환
  df_filled$date <- as.Date(df_filled$date)
  end_date <- as.Date("2025-01-31")
  
  # 사용자-앱별로 나누기
  user_app_list <- df_filled %>%
    group_by(user_id, app_name) %>%
    group_split()
  
  # 결과 저장
  results <- list()
  
  for (group in user_app_list) {
    user_id <- unique(group$user_id)
    app_name <- unique(group$app_name)
    age <- unique(group$age)
    category <- unique(group$category)
    
    used_dates <- group %>% filter(total_time > 0) %>% pull(date) %>% unique() %>% sort()
    
    # 기본값 설정
    dropout <- 0
    
    if (length(used_dates) > 0) {
      # 7일 중 3일 이상 사용 구간 존재 여부
      has_3in7 <- FALSE
      for (i in 1:length(used_dates)) {
        window <- used_dates[i] + 0:6
        if (sum(window %in% used_dates) >= 3) {
          has_3in7 <- TRUE
          break
        }
      }
      
      if (has_3in7) {
        last_used <- max(used_dates)
        
        # future_dates 생성 시 오류 방지
        if (last_used + 1 <= end_date - 2) {  # 최소 3일 연속 확인 필요
          future_dates <- seq.Date(last_used + 1, end_date, by = "1 day")
          future_use <- future_dates %in% used_dates
          
          # 마지막 사용일 이후 3일 연속 미사용 + 종료일까지 다시 사용 안 함
          if (length(future_use) >= 3 && !any(future_use[1:3]) && !any(future_use)) {
            dropout <- 1
          }
        }
      }
    }
    
    # 통계 요약
    total_usage <- sum(group$total_time)
    total_days <- n_distinct(group$date)
    avg_daily_usage <- ifelse(total_days > 0, total_usage / total_days, 0)
    usage_days <- sum(group$total_time > 0)
    
    results[[length(results) + 1]] <- data.frame(
      user_id = user_id,
      app_name = app_name,
      dropout = dropout,
      avg_daily_usage = avg_daily_usage,
      age = age,
      category = category,
      usage_days = usage_days
    )
  }
  
  # 데이터 결합
  category_analysis <- bind_rows(results)
  
  # 앱별 통제변수 계산 후 병합
  app_stats <- category_analysis %>%
    group_by(app_name) %>%
    summarise(
      user_count = n_distinct(user_id),
      avg_age_app = mean(age),
      avg_usage_days_app = mean(usage_days)
    )
  
  category_analysis <- category_analysis %>%
    left_join(app_stats, by = "app_name")
  
  # 회귀 분석
  category_analysis$category <- as.factor(category_analysis$category)
  
  model <- glm(dropout ~ category + avg_daily_usage + age +
                 user_count + avg_usage_days_app,
               data = category_analysis,
               family = binomial)
  
  summary(model)
  # 카테고리별 dropout 비율 시각화
  ggplot(category_analysis, aes(x = category, y = dropout)) +
    stat_summary(fun = mean, geom = "bar", fill = "steelblue") +
    labs(title = "Dropout Rate by App Category",
         x = "App Category", y = "Dropout Rate (Proportion)") +
    ylim(0, 1) +
    theme_minimal()  
  
  #회귀분석 : 가설 3
  # 1. 패키지 로드
  library(dplyr)
  library(lubridate)
  library(ggplot2)
  library(tidyr)
  library(stringr)
  library(zoo)
  
  # 2. 데이터 사용
  df <- df_filled
  df$date <- as.Date(df$date)
  
  # 3. SNS 앱 필터링
  sns_df <- df %>% filter(category == "SNS")
  
  # 4. 사용자별 이탈 여부 판단 함수
  get_dropout_flag <- function(user_data, end_date) {
    user_data <- user_data %>% arrange(date) %>%
      mutate(used = ifelse(total_time > 0, 1, 0))
    
    all_dates <- data.frame(date = seq(min(user_data$date), end_date, by = "day"))
    user_ts <- left_join(all_dates, user_data, by = "date") %>%
      mutate(user_id = unique(user_data$user_id),
             total_time = ifelse(is.na(total_time), 0, total_time),
             used = ifelse(total_time > 0, 1, 0))
    
    window_ok <- zoo::rollapply(user_ts$used, width = 7, FUN = function(x) sum(x) >= 3, align = "left", fill = FALSE)
    if (!any(window_ok)) return(0)
    
    last_use_day <- max(user_ts$date[user_ts$used == 1])
    after_last_use <- user_ts %>% filter(date > last_use_day)
    if (nrow(after_last_use) < 3) return(0)
    
    after_last_use$used_flag <- ifelse(after_last_use$total_time > 0, 1, 0)
    run_lengths <- rle(after_last_use$used_flag)
    
    if (any(run_lengths$values == 0 & run_lengths$lengths >= 3) &&
        sum(after_last_use$used_flag) == 0) {
      return(1)
    } else {
      return(0)
    }
  }
  
  # 5. 이탈 여부 계산 + 이탈 전 cutoff date 저장 ## [변경됨]
  end_date <- as.Date("2025-01-31")
  
  dropout_info <- sns_df %>%
    group_by(user_id) %>%
    group_split() %>%
    lapply(function(user_data) {
      user_data <- user_data %>% arrange(date) %>% mutate(used = ifelse(total_time > 0, 1, 0))
      all_dates <- data.frame(date = seq(min(user_data$date), end_date, by = "day"))
      user_ts <- left_join(all_dates, user_data, by = "date") %>%
        mutate(user_id = unique(user_data$user_id),
               total_time = ifelse(is.na(total_time), 0, total_time),
               used = ifelse(total_time > 0, 1, 0))
      
      window_ok <- zoo::rollapply(user_ts$used, width = 7, FUN = function(x) sum(x) >= 3, align = "left", fill = FALSE)
      if (!any(window_ok)) return(data.frame(user_id = unique(user_data$user_id), is_dropout = 0, cutoff_date = end_date))
      
      last_use_day <- max(user_ts$date[user_ts$used == 1])
      after_last_use <- user_ts %>% filter(date > last_use_day)
      if (nrow(after_last_use) < 3) return(data.frame(user_id = unique(user_data$user_id), is_dropout = 0, cutoff_date = end_date))
      
      after_last_use$used_flag <- ifelse(after_last_use$total_time > 0, 1, 0)
      run_lengths <- rle(after_last_use$used_flag)
      
      if (any(run_lengths$values == 0 & run_lengths$lengths >= 3) &&
          sum(after_last_use$used_flag) == 0) {
        return(data.frame(user_id = unique(user_data$user_id), is_dropout = 1, cutoff_date = last_use_day))
      } else {
        return(data.frame(user_id = unique(user_data$user_id), is_dropout = 0, cutoff_date = end_date))
      }
    }) %>%
    bind_rows()
  
  # 6. 사용자 속성
  user_info <- df %>% distinct(user_id, age)
  
  # 7. 이탈 전까지만 누적 SNS 사용량 계산 ## [변경됨]
  sns_usage <- sns_df %>%
    left_join(dropout_info, by = "user_id") %>%
    filter(date <= cutoff_date) %>%
    group_by(user_id) %>%
    summarise(sns_time = sum(total_time, na.rm = TRUE))
  
  # 8. 작심삼일 앱 기준 변수들: 이탈 전까지만 계산 ## [변경됨]
  jaksim_df <- df %>% filter(is_jaksim == 1)
  
  jaksim_with_cut <- jaksim_df %>%
    left_join(dropout_info, by = "user_id") %>%
    filter(date <= cutoff_date)
  
  avg_session_time <- jaksim_with_cut %>%
    group_by(user_id) %>%
    summarise(avg_session_time = mean(total_time, na.rm = TRUE))
  
  app_count <- jaksim_with_cut %>%
    group_by(user_id) %>%
    summarise(app_count = n_distinct(app_name))
  
  usage_duration <- jaksim_with_cut %>%
    group_by(user_id) %>%
    summarise(usage_duration = as.numeric(max(date) - min(date)) + 1)
  
  # 9. 통합 및 상호작용 항 생성
  model_df <- dropout_info %>%
    left_join(user_info, by = "user_id") %>%
    left_join(sns_usage, by = "user_id") %>%
    left_join(avg_session_time, by = "user_id") %>%
    left_join(app_count, by = "user_id") %>%
    left_join(usage_duration, by = "user_id") %>%
    mutate(age_x_sns = age * sns_time)
  
  # 10. NA 처리
  model_df[is.na(model_df)] <- 0
  
  # 11. 로지스틱 회귀
  model <- glm(is_dropout ~ sns_time + age + age_x_sns +
                 avg_session_time + app_count + usage_duration,
               data = model_df, family = "binomial")
  
  # 12. 결과 출력
  summary(model)
  
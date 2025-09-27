-- CREATE TABLE CMP_INFO (
--     CMP_NUM VARCHAR(10)PRIMARY KEY,                  -- 사업장번호
--     CMP_NM VARCHAR(100) NOT NULL,             -- 회사명
--     CMP_INDUSTRY VARCHAR(20),                 -- 업종
--     CMP_SECTOR VARCHAR(20),                   -- 산업
--     CMP_ADDR VARCHAR(200),                    -- 회사 주소
--     CMP_EXTEMP INT,                           -- 사외 이사회 수
--     CMP_ETHICS_YN VARCHAR(1),                 -- 윤리경영 여부 (Y/N)
--     CMP_COMP_YN VARCHAR(1)                    -- 컴플라이언스 정책 존재 여부 (Y/N)
-- );

-- COMMENT ON TABLE CMP_INFO IS '회사 기본 정보 테이블';

-- COMMENT ON COLUMN CMP_INFO.CMP_NUM IS '사업장번호 (PK)';
-- COMMENT ON COLUMN CMP_INFO.CMP_NM IS '회사명';
-- COMMENT ON COLUMN CMP_INFO.CMP_INDUSTRY IS '업종';
-- COMMENT ON COLUMN CMP_INFO.CMP_SECTOR IS '산업';
-- COMMENT ON COLUMN CMP_INFO.CMP_ADDR IS '회사 주소';
-- COMMENT ON COLUMN CMP_INFO.CMP_EXTEMP IS '사외 이사회 수';
-- COMMENT ON COLUMN CMP_INFO.CMP_ETHICS_YN IS '윤리경영 여부 (Y/N)';
-- COMMENT ON COLUMN CMP_INFO.CMP_COMP_YN IS '컴플라이언스 정책 존재 여부 (Y/N)';



-- INSERT INTO cmp_info (
--     cmp_num, cmp_nm, cmp_industry, cmp_sector,
--     cmp_addr, cmp_extemp, cmp_ethics_yn, cmp_comp_yn
-- ) VALUES
-- ('6182618882', '국민AI 주식회사', '서비스', '소프트웨어개발 및 공급',
--  '서울특별시 성북구 정릉로 77', 18, 'Y', 'Y');
 
 
 
 
 
--  CREATE TABLE EMP_INFO (
--     EMP_ID INT PRIMARY KEY,                   -- 사번 (PK)
--     EMP_NM VARCHAR(10) NOT NULL,              -- 이름
--     EMP_BIRTH VARCHAR(8),                     -- 생년월일 (YYYYMMDD)
--     EMP_TEL VARCHAR(20),                      -- 전화번호
--     EMP_EMAIL VARCHAR(20),                    -- 이메일
--     EMP_JOIN VARCHAR(8),                      -- 입사년도 (YYYYMMDD)
--     EMP_ACIDENT_CNT INT,                      -- 산재발생횟수
--     EMP_BOARD_YN VARCHAR(1),                  -- 이사회 여부 (Y/N)
--     EMP_GENDER VARCHAR(1)                     -- 성별 (남1, 여2)
-- );

-- COMMENT ON TABLE EMP_INFO IS '직원 기본 정보 테이블';

-- COMMENT ON COLUMN EMP_INFO.EMP_ID IS '사번 (PK)';
-- COMMENT ON COLUMN EMP_INFO.EMP_NM IS '이름';
-- COMMENT ON COLUMN EMP_INFO.EMP_BIRTH IS '생년월일 (YYYYMMDD)';
-- COMMENT ON COLUMN EMP_INFO.EMP_TEL IS '전화번호';
-- COMMENT ON COLUMN EMP_INFO.EMP_EMAIL IS '이메일';
-- COMMENT ON COLUMN EMP_INFO.EMP_JOIN IS '입사년도 (YYYYMMDD)';
-- COMMENT ON COLUMN EMP_INFO.EMP_ACIDENT_CNT IS '산재발생횟수';
-- COMMENT ON COLUMN EMP_INFO.EMP_BOARD_YN IS '이사회 여부 (Y/N)';
-- COMMENT ON COLUMN EMP_INFO.EMP_GENDER IS '성별 (남=1, 여=2)';


-- INSERT INTO emp_info (
--     emp_id, emp_nm, emp_birth, emp_tel,
--     emp_email, emp_join, emp_acident_cnt,
--     emp_board_yn, emp_gender
-- ) VALUES
-- (1, '김예진', '20000420', '01099256631',
--  'kimyj6631@naver.com', '20230302', 0,
--  'N', '2');


-- INSERT INTO emp_info (
--     emp_id, emp_nm, emp_birth, emp_tel,
--     emp_email, emp_join, emp_acident_cnt,
--     emp_board_yn, emp_gender
-- ) VALUES
-- (2, '손현호', '19990101', '01071899399',
--  'hhson@naver.com', '20240101', 0,
--  'N', '1');


-- INSERT INTO emp_info (
--     emp_id, emp_nm, emp_birth, emp_tel,
--     emp_email, emp_join, emp_acident_cnt,
--     emp_board_yn, emp_gender
-- ) VALUES
-- (3, '김경엽', '19980101', '01088739203',
--  'gykim@naver.com', '20240302', 0,
--  'N', '1');


-- INSERT INTO emp_info (
--     emp_id, emp_nm, emp_birth, emp_tel,
--     emp_email, emp_join, emp_acident_cnt,
--     emp_board_yn, emp_gender
-- ) VALUES
-- (4, '이종철', '1997', '01012329984',
--  'kimyj6631@naver.com', '20230302', 0,
--  'Y', '1');
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
--  CREATE TABLE ENV (	
--     YEAR INT PRIMARY KEY,                     -- 년도 (YYYY)	
--     ENERGY_USE FLOAT,                         -- 에너지 사용량	
--     GREEN_USE FLOAT,                          -- 온실가스 배출량	
--     RENEWABLE_YN VARCHAR(1),                  -- 재생에너지 사용여부 (Y/N)	
--     RENEWABLE_RATIO DECIMAL(5,3)              -- 재생에너지 비율	
-- );	
	
-- COMMENT ON TABLE ENV IS '환경현황 테이블';	
	
-- COMMENT ON COLUMN ENV.YEAR IS '년도 (PK, YYYY)';	
-- COMMENT ON COLUMN ENV.ENERGY_USE IS '에너지 사용량';	
-- COMMENT ON COLUMN ENV.GREEN_USE IS '온실가스 배출량';	
-- COMMENT ON COLUMN ENV.RENEWABLE_YN IS '재생에너지 사용여부 (Y/N)';	
-- COMMENT ON COLUMN ENV.RENEWABLE_RATIO IS '재생에너지 비율';	
	
	
	
	
-- INSERT INTO env (year, energy_use, green_use, renewable_yn, renewable_ratio) VALUES	
-- (2019, 10500.25, 4800.10, 'N', 0.120),	
-- (2020, 9800.75, 4500.55, 'Y', 0.215),	
-- (2021, 11020.40, 4700.30, 'Y', 0.285),	
-- (2022, 12500.60, 5000.20, 'Y', 0.180),	
-- (2023, 13250.80, 5100.00, 'Y', 0.325),	
-- (2024, 14000.00, 4950.75, 'Y', 0.410);	




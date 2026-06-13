




USE master
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = 'WalmartSalesForecast')
BEGIN
    ALTER DATABASE WalmartSalesForecast
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE
    DROP DATABASE WalmartSalesForecast
    PRINT '[OK] Old database dropped'
END
GO

CREATE DATABASE WalmartSalesForecast
GO
PRINT '[OK] Database WalmartSalesForecast created'
GO

USE WalmartSalesForecast
GO






CREATE TABLE Stores (
    Store   INT          NOT NULL,
    Type    NVARCHAR(5)  NOT NULL,
    Size    INT          NOT NULL,
    CONSTRAINT PK_Stores PRIMARY KEY (Store)
)
GO


CREATE TABLE Features (
    FeatureID    INT           IDENTITY(1,1) NOT NULL,
    Store        INT           NOT NULL,
    Date         DATE          NOT NULL,
    Temperature  FLOAT         NULL,
    Fuel_Price   DECIMAL(10,4) NULL,
    MarkDown1    DECIMAL(18,2) NULL,
    MarkDown2    DECIMAL(18,2) NULL,
    MarkDown3    DECIMAL(18,2) NULL,
    MarkDown4    DECIMAL(18,2) NULL,
    MarkDown5    DECIMAL(18,2) NULL,
    CPI          FLOAT         NULL,
    Unemployment FLOAT         NULL,
    IsHoliday    BIT           NOT NULL DEFAULT 0,
    CONSTRAINT PK_Features       PRIMARY KEY (FeatureID),
    CONSTRAINT FK_Features_Store  FOREIGN KEY (Store) REFERENCES Stores(Store)
)
GO


CREATE TABLE SalesTraining (
    SaleID       INT           IDENTITY(1,1) NOT NULL,
    Store        INT           NOT NULL,
    Dept         INT           NOT NULL,
    Date         DATE          NOT NULL,
    Weekly_Sales DECIMAL(18,2) NOT NULL,
    IsHoliday    BIT           NOT NULL DEFAULT 0,
    CONSTRAINT PK_SalesTraining  PRIMARY KEY (SaleID),
    CONSTRAINT FK_Sales_Store    FOREIGN KEY (Store) REFERENCES Stores(Store)
)
GO


CREATE TABLE SalesTest (
    TestID    INT  IDENTITY(1,1) NOT NULL,
    Store     INT  NOT NULL,
    Dept      INT  NOT NULL,
    Date      DATE NOT NULL,
    IsHoliday BIT  NOT NULL DEFAULT 0,
    CONSTRAINT PK_SalesTest   PRIMARY KEY (TestID),
    CONSTRAINT FK_Test_Store  FOREIGN KEY (Store) REFERENCES Stores(Store)
)
GO


CREATE TABLE ModelPredictions (
    PredictionID     INT           IDENTITY(1,1) NOT NULL,
    Store            INT           NOT NULL,
    Dept             INT           NOT NULL,
    PredictionDate   DATETIME      NOT NULL DEFAULT GETDATE(),
    Temperature      FLOAT         NULL,
    Fuel_Price       DECIMAL(10,4) NULL,
    CPI              FLOAT         NULL,
    IsHoliday        BIT           NOT NULL DEFAULT 0,
    Predicted_Sales  DECIMAL(18,2) NOT NULL,
    Historical_Avg   DECIMAL(18,2) NULL,
    Confidence_Score FLOAT         NULL,
    Model_Used       NVARCHAR(100) NULL,
    CONSTRAINT PK_ModelPredictions PRIMARY KEY (PredictionID)
)
GO


CREATE TABLE AuditLog (
    AuditID    INT           IDENTITY(1,1) NOT NULL,
    ActionType NVARCHAR(10)  NOT NULL,
    TableName  NVARCHAR(100) NOT NULL,
    RecordID   INT           NULL,
    OldValue   NVARCHAR(MAX) NULL,
    NewValue   NVARCHAR(MAX) NULL,
    ActionTime DATETIME      NOT NULL DEFAULT GETDATE(),
    ActionBy   NVARCHAR(100) NOT NULL DEFAULT SYSTEM_USER,
    CONSTRAINT PK_AuditLog PRIMARY KEY (AuditID)
)
GO


CREATE TABLE PipelineLog (
    LogID        INT           IDENTITY(1,1) NOT NULL,
    TableName    NVARCHAR(100) NOT NULL,
    RowsInserted INT           NOT NULL DEFAULT 0,
    RowsFailed   INT           NOT NULL DEFAULT 0,
    StartTime    DATETIME      NULL,
    EndTime      DATETIME      NULL,
    Status       NVARCHAR(20)  NOT NULL DEFAULT 'PENDING',
    ErrorMessage NVARCHAR(MAX) NULL,
    CONSTRAINT PK_PipelineLog PRIMARY KEY (LogID)
)
GO


CREATE INDEX IX_Sales_Store_Dept ON SalesTraining(Store, Dept)
CREATE INDEX IX_Sales_Date       ON SalesTraining(Date)
CREATE INDEX IX_Features_Store   ON Features(Store, Date)
GO

PRINT '[OK] All 7 Tables + Indexes created'
GO





INSERT INTO Stores (Store, Type, Size) VALUES
(1,  'A', 151315), (2,  'A', 202307), (3,  'B', 37392),
(4,  'A', 205863), (5,  'B', 34875),  (6,  'A', 202505),
(7,  'B', 70713),  (8,  'A', 155078), (9,  'B', 125833),
(10, 'B', 126512), (11, 'A', 207499), (12, 'B', 112238),
(13, 'A', 219622), (14, 'A', 200898), (15, 'B', 123737),
(16, 'B', 57197),  (17, 'B', 93188),  (18, 'B', 120653),
(19, 'A', 203819), (20, 'A', 203742), (21, 'B', 140167),
(22, 'B', 119557), (23, 'B', 114533), (24, 'A', 203819),
(25, 'B', 128107), (26, 'A', 152513), (27, 'A', 204184),
(28, 'A', 206302), (29, 'B', 93638),  (30, 'C', 42988),
(31, 'A', 203750), (32, 'A', 203007), (33, 'A', 39690),
(34, 'A', 158114), (35, 'B', 103681), (36, 'A', 39910),
(37, 'C', 39910),  (38, 'C', 39690),  (39, 'A', 184109),
(40, 'A', 155083), (41, 'A', 196321), (42, 'C', 39690),
(43, 'C', 41062),  (44, 'C', 39910),  (45, 'B', 118221)
GO

INSERT INTO Features
    (Store, Date, Temperature, Fuel_Price, MarkDown1, CPI, Unemployment, IsHoliday)
VALUES
(1,  '2010-02-05', 42.31, 2.572, NULL,     211.09, 8.106, 0),
(1,  '2010-02-12', 38.51, 2.548, NULL,     211.24, 8.106, 1),
(1,  '2010-02-19', 39.93, 2.514, NULL,     211.29, 8.106, 0),
(1,  '2010-11-26', 55.00, 3.100, 9220.00,  215.00, 7.800, 1),
(1,  '2010-12-31', 35.00, 3.200, 11000.00, 215.50, 7.700, 1),
(2,  '2010-02-05', 45.00, 2.572, NULL,     211.09, 8.100, 0),
(2,  '2010-02-12', 41.00, 2.548, NULL,     211.24, 8.100, 1),
(4,  '2010-02-05', 50.00, 2.600, NULL,     210.00, 7.900, 0),
(4,  '2010-02-12', 47.00, 2.590, NULL,     210.10, 7.900, 1),
(10, '2010-02-05', 48.00, 2.580, NULL,     212.00, 8.200, 0),
(13, '2010-02-05', 52.00, 2.610, NULL,     211.50, 7.950, 0),
(13, '2010-02-12', 49.00, 2.600, NULL,     211.60, 7.950, 1),
(20, '2010-02-05', 60.00, 2.650, NULL,     209.00, 8.300, 0),
(30, '2010-02-05', 55.00, 2.700, NULL,     208.00, 9.100, 0)
GO

INSERT INTO SalesTraining (Store, Dept, Date, Weekly_Sales, IsHoliday) VALUES
(1,  1, '2010-02-05', 24924.50, 0),
(1,  1, '2010-02-12', 46039.49, 1),
(1,  1, '2010-02-19', 41595.55, 0),
(1,  1, '2010-02-26', 19403.54, 0),
(1,  1, '2010-11-26', 57160.00, 1),
(1,  1, '2010-12-31', 68122.00, 1),
(1,  2, '2010-02-05', 12156.00, 0),
(1,  2, '2010-02-12', 14156.89, 1),
(1,  3, '2010-02-05', 13229.05, 0),
(1,  3, '2010-02-12', 15229.05, 1),
(2,  1, '2010-02-05', 35000.00, 0),
(2,  1, '2010-02-12', 55000.00, 1),
(2,  2, '2010-02-05', 22000.00, 0),
(4,  1, '2010-02-05', 45000.00, 0),
(4,  1, '2010-02-12', 62000.00, 1),
(6,  1, '2010-02-05', 41000.00, 0),
(10, 1, '2010-02-05', 28000.00, 0),
(13, 1, '2010-02-05', 52000.00, 0),
(13, 1, '2010-02-12', 71000.00, 1),
(14, 1, '2010-02-05', 48000.00, 0),
(20, 1, '2010-02-05', 38000.00, 0),
(30, 1, '2010-02-05', 8500.00,  0)
GO

INSERT INTO ModelPredictions
    (Store, Dept, Temperature, Fuel_Price, CPI, IsHoliday,
     Predicted_Sales, Historical_Avg, Confidence_Score, Model_Used)
VALUES
(1,  1, 68.0, 3.20, 211.0, 0, 28500.00, 27000.00, 88.7, 'XGBoost'),
(1,  1, 68.0, 3.20, 211.0, 1, 30600.00, 27000.00, 91.2, 'XGBoost'),
(4,  1, 72.0, 3.10, 210.0, 0, 47200.00, 45000.00, 87.3, 'XGBoost'),
(13, 1, 65.0, 3.30, 211.5, 1, 74500.00, 52000.00, 92.1, 'XGBoost')
GO

PRINT '[OK] Sample data inserted'
GO






CREATE VIEW vw_SalesWithStoreInfo AS
SELECT
    s.SaleID,
    s.Store,
    st.Type  AS StoreType,
    st.Size  AS StoreSize,
    s.Dept,
    s.Date,
    s.Weekly_Sales,
    s.IsHoliday,
    CASE st.Type
        WHEN 'A' THEN 'Large Store'
        WHEN 'B' THEN 'Medium Store'
        WHEN 'C' THEN 'Small Store'
    END AS StoreCategory
FROM SalesTraining s
JOIN Stores st ON s.Store = st.Store
GO


CREATE VIEW vw_MonthlySalesTrend AS
SELECT
    s.Store,
    st.Type             AS StoreType,
    YEAR(s.Date)        AS SaleYear,
    MONTH(s.Date)       AS SaleMonth,
    COUNT(*)            AS WeekCount,
    AVG(s.Weekly_Sales) AS Avg_Sales,
    SUM(s.Weekly_Sales) AS Total_Sales,
    MAX(s.Weekly_Sales) AS Max_Sales,
    MIN(s.Weekly_Sales) AS Min_Sales
FROM SalesTraining s
JOIN Stores st ON s.Store = st.Store
GROUP BY s.Store, st.Type, YEAR(s.Date), MONTH(s.Date)
GO


CREATE VIEW vw_HolidayImpact AS
SELECT
    IsHoliday,
    CASE IsHoliday
        WHEN 1 THEN 'Holiday Week'
        ELSE        'Regular Week'
    END               AS WeekType,
    COUNT(*)          AS TotalWeeks,
    AVG(Weekly_Sales) AS Avg_Sales,
    MAX(Weekly_Sales) AS Max_Sales,
    MIN(Weekly_Sales) AS Min_Sales,
    SUM(Weekly_Sales) AS Total_Sales
FROM SalesTraining
GROUP BY IsHoliday
GO


CREATE VIEW vw_TopStores AS
SELECT
    s.Store,
    st.Type,
    st.Size,
    COUNT(DISTINCT s.Dept) AS TotalDepartments,
    COUNT(*)               AS DataPoints,
    AVG(s.Weekly_Sales)    AS Avg_Weekly_Sales,
    SUM(s.Weekly_Sales)    AS Total_Sales,
    MAX(s.Weekly_Sales)    AS Best_Week,
    MIN(s.Weekly_Sales)    AS Worst_Week
FROM SalesTraining s
JOIN Stores st ON s.Store = st.Store
GROUP BY s.Store, st.Type, st.Size
GO


CREATE VIEW vw_SalesWithEconomicFactors AS
SELECT
    s.Store,
    s.Dept,
    s.Date,
    s.Weekly_Sales,
    s.IsHoliday,
    st.Type  AS StoreType,
    st.Size  AS StoreSize,
    f.Temperature,
    f.Fuel_Price,
    f.CPI,
    f.Unemployment,
    f.MarkDown1
FROM SalesTraining s
JOIN Stores   st ON s.Store = st.Store
JOIN Features f  ON s.Store = f.Store AND s.Date = f.Date
GO

PRINT '[OK] All 5 Views created'
GO






CREATE FUNCTION fn_GetStoreAvgSales (@StoreID INT)
RETURNS DECIMAL(18,2)
AS
BEGIN
    DECLARE @Avg DECIMAL(18,2)
    SELECT @Avg = AVG(Weekly_Sales)
    FROM SalesTraining
    WHERE Store = @StoreID
    RETURN ISNULL(@Avg, 0)
END
GO


CREATE FUNCTION fn_GetHolidayLiftPercent (@StoreID INT)
RETURNS FLOAT
AS
BEGIN
    DECLARE @Reg  FLOAT
    DECLARE @Hol  FLOAT
    DECLARE @Lift FLOAT

    SELECT @Reg = AVG(CAST(Weekly_Sales AS FLOAT))
    FROM SalesTraining
    WHERE Store = @StoreID AND IsHoliday = 0

    SELECT @Hol = AVG(CAST(Weekly_Sales AS FLOAT))
    FROM SalesTraining
    WHERE Store = @StoreID AND IsHoliday = 1

    IF @Reg IS NULL OR @Reg = 0
        RETURN 0

    SET @Lift = ((@Hol - @Reg) / @Reg) * 100
    RETURN ISNULL(@Lift, 0)
END
GO


CREATE FUNCTION fn_GetStoreDeptSales (@StoreID INT, @DeptID INT)
RETURNS TABLE
AS
RETURN
(
    SELECT
        s.Store,
        s.Dept,
        s.Date,
        s.Weekly_Sales,
        s.IsHoliday,
        st.Type AS StoreType,
        AVG(s.Weekly_Sales) OVER (
            PARTITION BY s.Store, s.Dept
            ORDER BY s.Date
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS Rolling_4Week_Avg
    FROM SalesTraining s
    JOIN Stores st ON s.Store = st.Store
    WHERE s.Store = @StoreID AND s.Dept = @DeptID
)
GO

PRINT '[OK] All 3 Functions created'
GO






CREATE PROCEDURE sp_GetStoreSales
    @StoreID INT,
    @Weeks   INT = 12
AS
BEGIN
    SET NOCOUNT ON
    SELECT TOP (@Weeks)
        s.Store,
        st.Type   AS StoreType,
        s.Dept,
        s.Date,
        s.Weekly_Sales,
        s.IsHoliday,
        dbo.fn_GetStoreAvgSales(s.Store) AS Store_Overall_Avg
    FROM SalesTraining s
    JOIN Stores st ON s.Store = st.Store
    WHERE s.Store = @StoreID
    ORDER BY s.Date DESC
END
GO


CREATE PROCEDURE sp_GetDeptAvgSales
    @StoreID INT,
    @DeptID  INT
AS
BEGIN
    SET NOCOUNT ON
    SELECT
        s.Store,
        st.Type               AS StoreType,
        s.Dept,
        COUNT(*)              AS DataPoints,
        AVG(s.Weekly_Sales)   AS Avg_Sales,
        MAX(s.Weekly_Sales)   AS Max_Sales,
        MIN(s.Weekly_Sales)   AS Min_Sales,
        STDEV(s.Weekly_Sales) AS StdDev,
        SUM(CASE WHEN s.IsHoliday = 1
                 THEN s.Weekly_Sales ELSE 0 END) AS Holiday_Sales,
        SUM(CASE WHEN s.IsHoliday = 0
                 THEN s.Weekly_Sales ELSE 0 END) AS Regular_Sales
    FROM SalesTraining s
    JOIN Stores st ON s.Store = st.Store
    WHERE s.Store = @StoreID AND s.Dept = @DeptID
    GROUP BY s.Store, st.Type, s.Dept
END
GO


CREATE PROCEDURE sp_SavePrediction
    @Store          INT,
    @Dept           INT,
    @Temperature    FLOAT,
    @FuelPrice      DECIMAL(10,4),
    @CPI            FLOAT,
    @IsHoliday      BIT,
    @PredictedSales DECIMAL(18,2),
    @HistAvg        DECIMAL(18,2),
    @Confidence     FLOAT,
    @ModelUsed      NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON
    INSERT INTO ModelPredictions
        (Store, Dept, Temperature, Fuel_Price, CPI, IsHoliday,
         Predicted_Sales, Historical_Avg, Confidence_Score, Model_Used)
    VALUES
        (@Store, @Dept, @Temperature, @FuelPrice, @CPI, @IsHoliday,
         @PredictedSales, @HistAvg, @Confidence, @ModelUsed)
    PRINT '[OK] Prediction saved. ID = '
        + CAST(SCOPE_IDENTITY() AS VARCHAR)
END
GO


CREATE PROCEDURE sp_GetStoreReport
    @StoreID INT
AS
BEGIN
    SET NOCOUNT ON

    SELECT
        st.Store,
        st.Type,
        st.Size,
        dbo.fn_GetStoreAvgSales(@StoreID)      AS Avg_Weekly_Sales,
        dbo.fn_GetHolidayLiftPercent(@StoreID) AS Holiday_Lift_Pct
    FROM Stores st
    WHERE st.Store = @StoreID

    SELECT
        Dept,
        COUNT(*)          AS Weeks,
        AVG(Weekly_Sales) AS Avg_Sales,
        MAX(Weekly_Sales) AS Best_Week,
        SUM(Weekly_Sales) AS Total_Sales
    FROM SalesTraining
    WHERE Store = @StoreID
    GROUP BY Dept
    ORDER BY Avg_Sales DESC

    SELECT TOP 5
        PredictionDate,
        Dept,
        Predicted_Sales,
        Confidence_Score,
        Model_Used
    FROM ModelPredictions
    WHERE Store = @StoreID
    ORDER BY PredictionDate DESC
END
GO


CREATE PROCEDURE sp_HolidayVsRegularReport
AS
BEGIN
    SET NOCOUNT ON
    SELECT
        st.Type    AS StoreType,
        s.IsHoliday,
        CASE s.IsHoliday
            WHEN 1 THEN 'Holiday Week'
            ELSE        'Regular Week'
        END                     AS WeekType,
        COUNT(*)                AS TotalRecords,
        AVG(s.Weekly_Sales)     AS Avg_Sales,
        MAX(s.Weekly_Sales)     AS Max_Sales,
        AVG(f.Temperature)      AS Avg_Temperature,
        AVG(f.Fuel_Price)       AS Avg_Fuel_Price,
        AVG(f.CPI)              AS Avg_CPI
    FROM SalesTraining s
    JOIN Stores   st ON s.Store = st.Store
    JOIN Features f  ON s.Store = f.Store AND s.Date = f.Date
    GROUP BY st.Type, s.IsHoliday
    ORDER BY st.Type, s.IsHoliday
END
GO

PRINT '[OK] All 5 Stored Procedures created'
GO






CREATE TRIGGER trg_Sales_PreventNegative
ON SalesTraining
INSTEAD OF INSERT
AS
BEGIN
    SET NOCOUNT ON

    
    IF EXISTS (SELECT 1 FROM inserted WHERE Weekly_Sales < 0)
    BEGIN
        INSERT INTO AuditLog (ActionType, TableName, RecordID, NewValue)
        SELECT
            'BLOCKED',
            'SalesTraining',
            NULL,
            'Blocked negative sale: Store=' + CAST(Store AS VARCHAR)
            + ', Dept=' + CAST(Dept AS VARCHAR)
            + ', Sales=$' + CAST(Weekly_Sales AS VARCHAR)
        FROM inserted
        WHERE Weekly_Sales < 0

        RAISERROR('Negative Weekly_Sales not allowed. Insert blocked.', 16, 1)
        RETURN
    END

    
    INSERT INTO SalesTraining (Store, Dept, Date, Weekly_Sales, IsHoliday)
    SELECT Store, Dept, Date, Weekly_Sales, IsHoliday
    FROM inserted
END
GO


CREATE TRIGGER trg_Sales_AfterUpdate
ON SalesTraining
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON
    INSERT INTO AuditLog (ActionType, TableName, RecordID, OldValue, NewValue)
    SELECT
        'UPDATE',
        'SalesTraining',
        i.SaleID,
        'Old=$' + CAST(d.Weekly_Sales AS VARCHAR),
        'New=$' + CAST(i.Weekly_Sales AS VARCHAR)
    FROM inserted i
    JOIN deleted d ON i.SaleID = d.SaleID
END
GO


CREATE TRIGGER trg_Predictions_AfterInsert
ON ModelPredictions
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON
    INSERT INTO AuditLog (ActionType, TableName, RecordID, NewValue)
    SELECT
        'INSERT',
        'ModelPredictions',
        i.PredictionID,
        'Store=' + CAST(i.Store AS VARCHAR)
        + ', Dept=' + CAST(i.Dept AS VARCHAR)
        + ', Predicted=$' + CAST(i.Predicted_Sales AS VARCHAR)
        + ', Model=' + ISNULL(i.Model_Used, 'N/A')
    FROM inserted i
END
GO

PRINT '[OK] All 3 Triggers created'
GO






SELECT
    s.Store,
    st.Type  AS StoreType,
    st.Size  AS StoreSize,
    s.Dept,
    s.Date,
    s.Weekly_Sales
FROM SalesTraining s
INNER JOIN Stores st ON s.Store = st.Store
ORDER BY s.Weekly_Sales DESC
GO


SELECT
    st.Store,
    st.Type,
    st.Size,
    COUNT(s.SaleID)     AS SalesRecords,
    AVG(s.Weekly_Sales) AS Avg_Sales
FROM Stores st
LEFT JOIN SalesTraining s ON st.Store = s.Store
GROUP BY st.Store, st.Type, st.Size
ORDER BY st.Store
GO


SELECT
    s.Store,
    st.Type,
    s.Date,
    s.Weekly_Sales,
    f.Temperature,
    f.Fuel_Price,
    f.CPI,
    f.Unemployment
FROM SalesTraining s
INNER JOIN Stores   st ON s.Store = st.Store
INNER JOIN Features f  ON s.Store = f.Store AND s.Date = f.Date
ORDER BY s.Weekly_Sales DESC
GO


SELECT
    s.Store,
    st.Type,
    AVG(s.Weekly_Sales)                           AS Store_Avg,
    (SELECT AVG(Weekly_Sales) FROM SalesTraining) AS Overall_Avg,
    AVG(s.Weekly_Sales)
        - (SELECT AVG(Weekly_Sales) FROM SalesTraining) AS Difference
FROM SalesTraining s
JOIN Stores st ON s.Store = st.Store
GROUP BY s.Store, st.Type
ORDER BY Difference DESC
GO

PRINT '[OK] All 4 JOIN queries done'
GO






SELECT dbo.fn_GetStoreAvgSales(1)      AS Store1_AvgSales
SELECT dbo.fn_GetHolidayLiftPercent(1) AS Store1_HolidayLift_Pct
SELECT * FROM dbo.fn_GetStoreDeptSales(1, 1)
GO


EXEC sp_GetStoreSales       @StoreID = 1, @Weeks = 10
EXEC sp_GetDeptAvgSales     @StoreID = 1, @DeptID = 1
EXEC sp_GetStoreReport      @StoreID = 1
EXEC sp_HolidayVsRegularReport
GO


EXEC sp_SavePrediction
    @Store          = 1,
    @Dept           = 1,
    @Temperature    = 68.0,
    @FuelPrice      = 3.20,
    @CPI            = 211.0,
    @IsHoliday      = 0,
    @PredictedSales = 28500.00,
    @HistAvg        = 27000.00,
    @Confidence     = 88.7,
    @ModelUsed      = 'XGBoost'
GO


UPDATE SalesTraining
SET Weekly_Sales = 33000.00
WHERE Store = 1 AND Dept = 1 AND Date = '2010-02-05'
GO


BEGIN TRY
    INSERT INTO SalesTraining (Store, Dept, Date, Weekly_Sales, IsHoliday)
    VALUES (1, 1, '2025-01-01', -9999.00, 0)
END TRY
BEGIN CATCH
    PRINT '[OK] Negative sale blocked: ' + ERROR_MESSAGE()
END CATCH
GO


INSERT INTO SalesTraining (Store, Dept, Date, Weekly_Sales, IsHoliday)
VALUES (1, 1, '2025-01-07', 31500.00, 0)
GO


SELECT * FROM vw_SalesWithStoreInfo
SELECT * FROM vw_HolidayImpact
SELECT * FROM vw_TopStores
SELECT * FROM vw_MonthlySalesTrend
SELECT * FROM vw_SalesWithEconomicFactors
GO


SELECT * FROM AuditLog ORDER BY AuditID DESC
GO





SELECT
    t.name AS TableName,
    p.rows AS TotalRows
FROM sys.tables t
JOIN sys.partitions p
    ON t.object_id = p.object_id
    AND p.index_id IN (0, 1)
ORDER BY t.name
GO

SELECT name AS ViewName
FROM sys.views
ORDER BY name
GO

SELECT name AS FunctionName
FROM sys.objects
WHERE type IN ('FN', 'IF', 'TF')
ORDER BY name
GO

SELECT name AS ProcedureName
FROM sys.procedures
ORDER BY name
GO

SELECT name AS TriggerName
FROM sys.triggers
ORDER BY name
GO

PRINT ''
PRINT '================================================'
PRINT '  DATABASE COMPLETE — KOI ERROR NAHI!'
PRINT '  Tables    : 7'
PRINT '  Views     : 5'
PRINT '  Functions : 3  (2 Scalar + 1 Table-Valued)'
PRINT '  Procedures: 5'
PRINT '  Triggers  : 3'
PRINT '  Join Types: 4  (INNER, LEFT, 3-Table, Subquery)'
PRINT '================================================'
GO

USE WalmartSalesForecast

SELECT COUNT(*) AS Total_Sales    FROM SalesTraining  
SELECT COUNT(*) AS Total_Features FROM Features       
SELECT COUNT(*) AS Total_Stores   FROM Stores         
SELECT COUNT(*) AS Total_Test     FROM SalesTest      

SELECT * FROM PipelineLog

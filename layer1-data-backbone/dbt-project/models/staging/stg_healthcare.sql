WITH source_data AS (
    -- Source: healthcare_dataset.csv (55,500 patient records)
    -- Loaded via dbt seed command
    SELECT
        "Name" AS patient_name,
        "Date of Admission" AS date_of_admission,
        "Discharge Date" AS discharge_date,
        "Age" AS age,
        "Gender" AS gender,
        "Blood Type" AS blood_type,
        "Medical Condition" AS medical_condition,
        "Medication" AS medication,
        "Test Results" AS test_results,
        "Admission Type" AS admission_type,
        "Doctor" AS doctor,
        "Hospital" AS hospital,
        "Insurance Provider" AS insurance_provider,
        "Billing Amount" AS billing_amount,
        "Room Number" AS room_number,
        "Date of Admission" AS admission_date_raw -- Keep raw for now, will cast later
    FROM {{ source('healthcare', 'raw_healthcare_data') }} -- Placeholder source
)

SELECT
    -- Generate surrogate key for encounter
    {{ dbt_utils.generate_surrogate_key(['patient_name', 'date_of_admission']) }} AS encounter_id,
    
    -- Hash PII for patient name (using SQL Server HASHBYTES)
    CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', patient_name), 2) AS patient_name_hash,

    -- Clean column names and type cast dates
    REPLACE(LOWER(patient_name), ' ', '_') AS patient_name_cleaned,
    CAST(date_of_admission AS DATE) AS admission_date,
    CAST(discharge_date AS DATE) AS discharge_date,
    age,
    gender,
    REPLACE(LOWER(blood_type), ' ', '_') AS blood_type,
    REPLACE(LOWER(medical_condition), ' ', '_') AS medical_condition,
    REPLACE(LOWER(medication), ' ', '_') AS medication,
    REPLACE(LOWER(test_results), ' ', '_') AS test_results,
    REPLACE(LOWER(admission_type), ' ', '_') AS admission_type,
    REPLACE(LOWER(doctor), ' ', '_') AS doctor_name,
    REPLACE(LOWER(hospital), ' ', '_') AS hospital_name,
    REPLACE(LOWER(insurance_provider), ' ', '_') AS insurance_provider,
    billing_amount,
    room_number
FROM source_data
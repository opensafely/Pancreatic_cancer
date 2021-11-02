from cohortextractor import StudyDefinition, patients, Measure, codelist, codelist_from_csv

from codelists import *

window_date = "2015-01-01"

study = StudyDefinition(
        default_expectations={
        "date": {"earliest": "1900-01-01", "latest": "today"},
        "rate": "uniform",
        "incidence": 0.5,
        },
    
    #index_date = "", will be cancer diagnosis for each pt
    
    population=patients.satisfying(
        """
        has_ca AND
        (age >=18 AND age <= 110)
        """,
        has_ca=patients.with_these_clinical_events(
        pan_cancer_codes,
        on_or_after=window_date ## this is to restrict to cases in the time window from Jan 2015
        )
    ),
    pa_ca=patients.with_these_clinical_events(
        pan_cancer_codes,
        on_or_after=window_date,
        find_last_match_in_period=True,
        include_date_of_match=True,
        include_month=True, 
        include_day=True,
        returning="binary_flag", # later could do it as cat for the type of pa ca
        return_expectations={"incidence": 1.0},
    ),
    #so the above code to extarct dates (we have everyone in this study sample with PaCa) work fine, 
    #gives dates for everyone, but no restriction in the dammy data on the time windeow of intererts
    # Pleae can you check my code and confirm that the poipulation "satifying" will take case of this?

    #The below code is anohter way of extarcting date of PaCa diagnosis - but it does not give me dates for everyone
    # Again a question, becasue everyone in real data will have diagnosis on or after 2015 will this then 
    # work in real data? 
    
    #also a quesiton there - on how do I find out when it was fist diagnosed?
    #I mean "find_first_match_in_period" is it the perios of 20125-present? 
    #so what if they had it first time codes before this time window? 
    ca_date=patients.with_these_clinical_events(
        pan_cancer_codes,
        on_or_after=window_date,
        find_first_match_in_period=True, # how do i find out when it was firt diagnosed 
        returning="date",
        date_format="YYYY-MM-DD",
        return_expectations={"incidence": 1.0},
    ),
    age=patients.age_as_of(
        "ca_date",
        return_expectations={
            "rate": "exponential_increase",
            "int": {"distribution": "population_ages"},
        },
    ),
    sex=patients.sex(
        return_expectations={
            "rate": "universal",
            "category": {"ratios": {"M": 0.49, "F": 0.51}},
        }
    ),
    ethnicity=patients.with_these_clinical_events(
        ethnicity_codes,
        returning="category",
        find_last_match_in_period=True,
        include_date_of_match=True,
        include_month=True, 
        include_day=True,
        return_expectations={
            "category": {"ratios": {"1": 0.8, "2": 0.01, "3": 0.01, "4": 0.18}},
            "incidence": 0.75,
        },
    ),
    stp=patients.registered_practice_as_of(
        "ca_date",
        returning="stp_code",
        return_expectations={
            "rate": "universal",
            "category": {"ratios": {"E54000005": 0.25, "E54000006": 0.25,
            "E54000007": 0.25, "E54000008": 0.25}},
        },
    ),
    region=patients.registered_practice_as_of(
        "ca_date",
        returning="nuts1_region_name",
        return_expectations={
            "rate": "universal",
            "category": {
                "ratios": {
                    "North East": 0.1,
                    "North West": 0.1,
                    "Yorkshire and the Humber": 0.2,
                    "East Midlands": 0.1,
                    "West Midlands": 0.1,
                    "East of England": 0.1,
                    "London": 0.1,
                    "South East": 0.2,
                },
            },
        },
    ),
    # IMD - quintile
    imd=patients.address_as_of(
        "ca_date",
        returning="index_of_multiple_deprivation",
        round_to_nearest=100,
        return_expectations={
        "rate": "universal",
        "category": {"ratios": {"100": 0.1, "200": 0.2, "300": 0.7}},
        },
    ),
    imd_quin=patients.categorised_as(
        {   "No data": "DEFAULT", #this is missing data? 
            "1": """index_of_multiple_deprivation >=1 AND index_of_multiple_deprivation < 32844*1/5""",
            "2": """index_of_multiple_deprivation >= 32844*1/5 AND index_of_multiple_deprivation < 32844*2/5""",
            "3": """index_of_multiple_deprivation >= 32844*2/5 AND index_of_multiple_deprivation < 32844*3/5""",
            "4": """index_of_multiple_deprivation >= 32844*3/5 AND index_of_multiple_deprivation < 32844*4/5""",
            "5": """index_of_multiple_deprivation >= 32844*4/5 AND index_of_multiple_deprivation < 32844""",
        },#took it from ?, is this the right way to calc quintiles? 
        index_of_multiple_deprivation=patients.address_as_of(
            "ca_date",
            returning="index_of_multiple_deprivation",
            round_to_nearest=100,
    ),
        return_expectations={
            "rate": "universal",
            "category": {
                "ratios": {
                    "No data": 0.2,
                    "1": 0.2,
                    "2": 0.2,
                    "3": 0.2,
                    "4": 0.1,
                    "5": 0.1,
                }
            },
        },
    ),
    # BMI
    bmi=patients.most_recent_bmi(
        between=["ca_date - 1 years", "ca_date + 1 years"],
        minimum_age_at_measurement=18,
        include_measurement_date=True,
        date_format="YYYY-MM-DD",
        return_expectations={
        "date": {"earliest": "2015-01-01", "latest": "today"},
        "float": {"distribution": "normal", "mean": 25, "stddev": 8},
        "incidence": 0.80
        }
    ),
    bmi_cat=patients.categorised_as(
        {   "No data": "DEFAULT",  
            "Underweight (<18.5)": """ bmi_value >= 5 AND bmi_value < 18.5""",
            "Normal (18.5-24.9)": """ bmi_value >= 18.5 AND bmi_value < 25""",
            "Overweight (25-29.9)": """ bmi_value >= 25 AND bmi_value < 30""",
            "Obese I (30-34.9)": """ bmi_value >= 30 AND bmi_value < 35""",
            "Obese II (35-39.9)": """ bmi_value >= 35 AND bmi_value < 40""",
            "Obese III (40+)": """ bmi_value >= 40 AND bmi_value < 100"""
        },
        bmi_value=patients.most_recent_bmi(
            between=["ca_date - 1 years", "ca_date + 1 years"],
            minimum_age_at_measurement=16
            ),
        return_expectations={
            "rate": "universal",
            "category": {
                "ratios": {
                    "No data": 0.2,
                    "Underweight (<18.5)": 0.2, #ppl lose a lot of weight when they are diagnosed with PaCa
                    "Normal (18.5-24.9)": 0.3,
                    "Overweight (25-29.9)": 0.1, 
                    "Obese I (30-34.9)": 0.1,
                    "Obese II (35-39.9)": 0.05,
                    "Obese III (40+)": 0.05,
                }
            }
        }
    ),
    latest_hba1c=patients.with_these_clinical_events(
        hba1c_new_codes,
        find_last_match_in_period=True,
        between=["ca_date - 1 years", "ca_date + 1 years"],
        returning="numeric_value", # how do I restrick on the possible range? To exclude impossible values? 
        include_date_of_match=True,
        include_month=True, 
        include_day=True,
        return_expectations={
        "float": {"distribution": "normal", "mean": 40.0, "stddev": 20},
        "incidence": 0.95,
        }
        #this code gives me 0 for missing values - is there a way to have NAs? 
    ),
    hba1c_date=patients.date_of("latest_hba1c", date_format="YYYY-MM-DD"),
        #hba1c_comparator=patients.comparator_from("latest_hba1c"),
        chemo_or_radio=patients.with_these_clinical_events(
        chemotherapy_or_radiotherapy_codes,
        on_or_before="today",
        returning="binary_flag",
        return_expectations={"incidence": 0.01,},
    ),
    #cancer variables 
    Referrals=patients.with_these_clinical_events(
        cancer_referral_codes,
        #on_or_before="ca_date",
        between=["ca_date - 6 months", "ca_date"],
        find_first_match_in_period=True, 
        returning="date",
        date_format="YYYY-MM-DD",
        return_expectations={"incidence": 0.6},
    ),

    admitted=patients.admitted_to_hospital(
        returning="binary_flag",
        between=["ca_date - 6 months", "ca_date + 6 months"],
        return_expectations={"incidence": 0.1}
        # retrieve the number of admissions? 
    ),
    ca_adm_date=patients.admitted_to_hospital(
        returning= "date_admitted",
        with_these_diagnoses=pa_ca_icd10,
        on_or_after="ca_date",
        find_first_match_in_period=True,
        date_format="YYYY-MM-DD",
        return_expectations={"date": {"earliest": "2015-01-01"}},
    ),
    emergency_care_before=patients.attended_emergency_care(
        between=["ca_date - 6 months", "ca_date"],
        returning="date_arrived",
        date_format="YYYY-MM-DD",
        find_first_match_in_period=True,
        return_expectations={
        "date": {"earliest" : "2014-06-01"},
        "rate" : "exponential_increase"
        },
    ),

    emergency_care_after=patients.attended_emergency_care(
        between=["ca_date", "ca_date + 6 months"],
        returning="date_arrived",
        date_format="YYYY-MM-DD",
        find_first_match_in_period=True,
        return_expectations={
        "date": {"earliest" : "2015-06-01"},
        "rate" : "exponential_increase"
        },
    ),

    died=patients.died_from_any_cause(
        on_or_after="ca_date",
        returning="binary_flag",
        return_expectations={"incidence": 0.80},
    ),

    died_any=patients.died_from_any_cause(
        on_or_after="ca_date",
        returning="date_of_death",
        date_format="YYYY-MM-DD",
        return_expectations={
        "date": {"earliest" : "2015-01-01"},
        "rate" : "exponential_increase",
        "incidence": 0.80
        },
    ),
    died_ca=patients.with_these_codes_on_death_certificate(
        pa_ca_icd10,
        on_or_after="ca_date",
        match_only_underlying_cause=False,
        return_expectations={
        "incidence": 0.50
        },
    ),
    died_ca_date=patients.with_these_codes_on_death_certificate(
        pa_ca_icd10,
        on_or_after="ca_date",
        match_only_underlying_cause=False,
        returning="date_of_death",
        date_format="YYYY-MM-DD",
        return_expectations={
        "date": {"earliest" : "2015-01-01"},
        "rate" : "exponential_increase",
        "incidence": 0.50
        },
    ),
    gp_count=patients.with_gp_consultations(
        between=["ca_date - 1 years", "ca_date"],
        returning="number_of_matches_in_period",
        return_expectations={
        "int": {"distribution": "normal", "mean": 6, "stddev": 3},
        "incidence": 0.6,
        },
    ),
    care_home_type=patients.care_home_status_as_of(
        "ca_date",
        categorised_as={
        "PC":
        """
          IsPotentialCareHome
          AND LocationDoesNotRequireNursing='Y'
          AND LocationRequiresNursing='N'
        """,
        "PN":
        """
          IsPotentialCareHome
          AND LocationDoesNotRequireNursing='N'
          AND LocationRequiresNursing='Y'
        """,
        "PS": "IsPotentialCareHome",
        "PR": "NOT IsPotentialCareHome",
        "": "DEFAULT",
        },
    return_expectations={
        "rate": "universal",
        "category": {"ratios": {"PC": 0.05, "PN": 0.05, "PS": 0.05, "PR": 0.84, "": 0.01},},
        },
    ),
    # hh_size=patients.household_as_of(
    # "2020-02-01", returning="household_size"
    # )
)
###2/11/21
import streamlit as st
import pandas as pd
import math
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(page_title="Vehicle Loan Eligibility Calculator", layout="centered")
st.title("🚗 Vehicle Loan Eligibility Calculator")
st.write("Check maximum loan eligibility based on customer type and income.")

# Customer type selection
customer_type = st.selectbox("Select Customer Type", [
    "Salaried", "Self-employed", "Pensioner", "Government/PSU Employee"
])

# Input fields
invoice_value = st.number_input("Vehicle Invoice Value (₹)", min_value=0.0, step=1000.0)
accessory_cost = st.number_input("Accessory Cost (₹, Max ₹25,000)", min_value=0.0, max_value=25000.0, step=500.0)
gross_annual_income = st.number_input("Gross Annual Income (₹)", min_value=0.0, step=10000.0)
avg_last_3_years_income = st.number_input("Avg Annual Income (Last 3 Years, ₹)", min_value=0.0, step=10000.0)
existing_emi = st.number_input("Existing EMI (₹ per month)", min_value=0.0, step=500.0)
interest_rate = st.number_input("Proposed Interest Rate (% p.a.)", min_value=0.0, step=0.1, value=9.0)
tenure_years = st.slider("Loan Tenure (in years) [Max 7 years]", min_value=1, max_value=7, value=5)

# Gross monthly salary
gross_monthly = gross_annual_income / 12

# Quantum Calculation
total_cost = invoice_value + min(accessory_cost, 25000)

# Margin based on type and cost
if customer_type == "Government/PSU Employee":
    if total_cost <= 1000000:
        margin_percent = 10
    elif total_cost <= 2500000:
        margin_percent = 10
    else:
        margin_percent = 20
else:
    if total_cost <= 1000000:
        margin_percent = 10
    elif total_cost <= 2500000:
        margin_percent = 15
    else:
        margin_percent = 20

margin_amount = total_cost * (margin_percent / 100)
loan_amount = total_cost - margin_amount

# EMI Calculation using standard EMI formula
months = tenure_years * 12
monthly_rate = interest_rate / (12 * 100)

if loan_amount > 0 and monthly_rate > 0:
    emi = loan_amount * monthly_rate * ((1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
else:
    emi = 0

# Recalculate net salary after existing and proposed EMI
net_salary_after_emi = gross_monthly - existing_emi - emi

# Eligibility check
eligible = False

if customer_type == "Salaried":
    if gross_annual_income >= 300000 and net_salary_after_emi >= max(0.25 * gross_monthly, 12000):
        eligible = True
elif customer_type == "Self-employed":
    if gross_annual_income >= 300000 and avg_last_3_years_income >= 250000 and net_salary_after_emi >= max(0.25 * gross_monthly, 12000):
        eligible = True
elif customer_type == "Government/PSU Employee":
    if gross_annual_income >= 300000 and net_salary_after_emi >= max(0.25 * gross_monthly, 12000):
        eligible = True
elif customer_type == "Pensioner":
    if gross_annual_income >= 300000 and net_salary_after_emi >= 0.5 * gross_monthly:
        eligible = True

# Output
st.markdown("---")
st.subheader("🧾 Loan Calculation Summary")
st.write(f"**Total Cost Considered:** ₹{total_cost:,.2f}")
st.write(f"**Margin ({margin_percent}%):** ₹{margin_amount:,.2f}")
st.write(f"**Eligible Loan Amount:** ₹{loan_amount:,.2f}")
st.write(f"**Estimated EMI (₹):** ₹{emi:,.2f}")

if eligible:
    st.success("✅ Customer is eligible for the vehicle loan.")
else:
    st.error("❌ Customer is NOT eligible based on income or EMI criteria.")

# Amortization Schedule
with st.expander("📅 Show Amortization Schedule"):
    if emi > 0:
        schedule = []
        balance = loan_amount
        total_interest = 0
        total_principal = 0

        for m in range(1, months + 1):
            interest = balance * monthly_rate
            principal = emi - interest
            balance -= principal
            total_interest += interest
            total_principal += principal
            schedule.append({
                "Month": m,
                "EMI": round(emi, 2),
                "Principal": round(principal, 2),
                "Interest": round(interest, 2),
                "Balance": round(max(balance, 0), 2)
            })

        df = pd.DataFrame(schedule)
        st.dataframe(df, use_container_width=True)

        # Downloadable Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Amortization')
            processed_data = output.getvalue()

        st.download_button(
            label="📥 Download Amortization Schedule (Excel)",
            data=processed_data,
            file_name="loan_amortization_schedule.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Pie Chart: Principal vs Interest
        fig, ax = plt.subplots()
        ax.pie([total_principal, total_interest], labels=["Principal", "Interest"], autopct='%1.1f%%', colors=["#4CAF50", "#FF9800"])
        ax.set_title("Principal vs Interest Payable")
        st.pyplot(fig)

    else:
        st.warning("EMI is not calculated yet. Please input valid loan details.")

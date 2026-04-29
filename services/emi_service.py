from core.models import SessionContext

LOANS24_RATE_PA = 0.1099          # 10.99% per annum
PROCESSING_FEE_RATE = 0.01        # 1% of loan amount


class EMIService:
    def calculate(
        self,
        price: int,
        tenure_months: int = 48,
        down_payment: int = 0,
        rate_pa: float = LOANS24_RATE_PA
    ) -> dict:
        loan_amount = price - down_payment
        r = rate_pa / 12          # monthly rate

        if r == 0:
            emi = loan_amount / tenure_months
        else:
            emi = loan_amount * r * \
                (1 + r)**tenure_months / ((1 + r)**tenure_months - 1)

        total_payable = emi * tenure_months
        total_interest = total_payable - loan_amount
        processing_fee = loan_amount * PROCESSING_FEE_RATE

        return {
            "loan_amount": round(loan_amount),
            "emi_monthly": round(emi),
            "tenure_months": tenure_months,
            "total_payable": round(total_payable),
            "total_interest": round(total_interest),
            "processing_fee": round(processing_fee),
            "rate_pa": rate_pa,
            "down_payment": down_payment,
        }

    def format_for_display(self, result: dict) -> str:
        return (
            f"₹{result['emi_monthly']:,}/month over {result['tenure_months']} months "
            f"at {result['rate_pa']*100:.2f}% p.a. "
            f"(₹0 down via LOANS24). "
            f"Total payable: ₹{result['total_payable']:,}"
        )

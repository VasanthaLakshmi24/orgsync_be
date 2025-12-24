from decimal import Decimal, ROUND_HALF_UP

def calculate_salary_components(ctc, basic_value, basic_type, allowance_percentages, pf):
    result = {}
    monthly_ctc = Decimal(ctc) / Decimal(12)

    
    if basic_type == 'percentage':
        basic = (Decimal(basic_value) / Decimal(100)) * monthly_ctc
    elif basic_type == 'amount':
        basic = Decimal(basic_value)

    
    hra_percentage = Decimal(60)
    hra = (hra_percentage / Decimal(100)) * basic

    
    remaining_ctc_for_allowances = monthly_ctc - basic - pf - hra

    
    allowance_amounts = {}
    if remaining_ctc_for_allowances > 0:
        total_allowance_percentage = Decimal(sum(allowance_percentages.values()))
        for allowance, percentage in allowance_percentages.items():
            allowance_amounts[allowance] = (Decimal(percentage) / total_allowance_percentage) * remaining_ctc_for_allowances

    
    allowance_amounts['HRA'] = hra

    
    gross_salary = basic + sum(allowance_amounts.values())

    
    esi = 0

    
    while True:
        
        total_deductions = pf + esi
        
        new_gross_salary = monthly_ctc - total_deductions

        
        new_esi = 0

        
        if new_gross_salary == gross_salary and new_esi == esi:
            break

        gross_salary = new_gross_salary
        esi = new_esi

    
    # result['Deductions'] = {"PF": pf, "ESI": esi.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)}
    result['TotalDeductions'] = total_deductions.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)

    
    result['FinalSummary'] = {
        'GrossSalary': gross_salary.quantize(Decimal('1.'), rounding=ROUND_HALF_UP),
        'BasicSalary': basic.quantize(Decimal('1.'), rounding=ROUND_HALF_UP),
        'Sumofallallowances': sum(allowance_amounts.values()).quantize(Decimal('1.'), rounding=ROUND_HALF_UP),
        'FinalPF': pf.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
    }

    result['Allowances'] = {k: v.quantize(Decimal('1.'), rounding=ROUND_HALF_UP) for k, v in allowance_amounts.items()}

    return result


ctc = 16667.00 * 12
basic_value = 50
basic_type = 'percentage'  
pf = Decimal(0)
allowance_percentages = {
    "Travel": 100,
}


salary_details = calculate_salary_components(ctc, basic_value, basic_type, allowance_percentages, pf)
print(salary_details)

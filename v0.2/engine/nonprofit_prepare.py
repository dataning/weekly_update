from dataclasses import dataclass
from typing import Dict
import polars as pl
import re

@dataclass
class Multi_IRS990_Forms:
    """Class to handle and analyze IRS 990 tax forms data.

    This class provides methods to load and analyze different sections of IRS 990 tax forms,
    including core form data, schedules, and various financial and personnel information.

    Args:
        ein: str
            Employer Identification Number (9-digit)
        dict_df: Dict[str, pl.DataFrame]
            Dictionary containing DataFrames with keys that match IRS form names
            (e.g., 'IRS990', 'IRS990ScheduleD', etc.)
    """

    ein: str
    core_df: pl.DataFrame
    schedule_d_df: pl.DataFrame
    schedule_a_df: pl.DataFrame
    schedule_j_df: pl.DataFrame
    return_header_df: pl.DataFrame
    MIN_YEAR: int = 2015

    def __init__(self, ein: str, dict_df: Dict[str, pl.DataFrame]):
        """Initialize with IRS 990 form dataframes for a given EIN.

        Args:
            ein: The Employer Identification Number (expected format: 9 digits)
            dict_df: Dictionary containing DataFrames for each form/schedule

        Raises:
            ValueError: If EIN format is invalid (not exactly 9 digits)
            KeyError: If required DataFrames are missing from dict_df
            ValueError: If required columns are missing in the loaded data
        """
        # Validate EIN format
        if not re.match(r'^\d{9}$', ein):
            raise ValueError(f"Invalid EIN format: {ein}. Expected exactly 9 digits.")

        self.ein = ein

        # Map form names to class attributes
        form_mapping = {
            'IRS990': 'core_df',
            'IRS990ScheduleD': 'schedule_d_df',
            'IRS990ScheduleA': 'schedule_a_df',
            'IRS990ScheduleJ': 'schedule_j_df',
            'ReturnHeader': 'return_header_df'
        }

        # Check if all required DataFrames are present
        missing_forms = [form for form in form_mapping.keys() if form not in dict_df]
        if missing_forms:
            raise KeyError(f"Missing required forms: {', '.join(missing_forms)}")

        # Filter and assign DataFrames
        for form_name, attr_name in form_mapping.items():
            filtered_df = (
                dict_df[form_name]
                .filter(pl.col('EIN') == ein)
                .with_columns([
                    pl.col('year').cast(pl.Int32, strict=False)
                ])
                .filter(pl.col('year') >= self.MIN_YEAR)
            )
            setattr(self, attr_name, filtered_df)

        # Ensure each DataFrame has required columns
        self._validate_dataframes()

    def _validate_dataframes(self) -> None:
        """Validate that each loaded DataFrame has the essential columns."""
        required_cols = {
            'core_df': {'EIN', 'year'},
            'schedule_d_df': {'EIN', 'year'},
            'schedule_a_df': {'EIN', 'year'},
            'schedule_j_df': {'EIN', 'year'},
            'return_header_df': {'EIN', 'year'},
        }

        dataframes = {
            'core_df': self.core_df,
            'schedule_d_df': self.schedule_d_df,
            'schedule_a_df': self.schedule_a_df,
            'schedule_j_df': self.schedule_j_df,
            'return_header_df': self.return_header_df,
        }

        for df_name, required in required_cols.items():
            missing = required - set(dataframes[df_name].columns)
            if missing:
                raise ValueError(
                    f"Missing required columns in {df_name}: {missing}"
                )

    def _extract_column_identifiers(
        self,
        columns: list[str],
        group_pattern: str,
        identifier_pattern: str = r'\[(\d+)\]'
    ) -> set[str]:
        """Extract unique identifiers from column names based on patterns."""
        identifiers = set()
        for col in columns:
            if group_pattern in col:
                match = re.search(identifier_pattern, col)
                if match:
                    identifiers.add(match.group(1))
        return identifiers

    def create_long_format_df(
        self,
        df: pl.DataFrame,
        group_pattern: str,
        base_cols: list[str] | None = None,
        attribute_mappings: Dict[str, str] | None = None,
        identifier_pattern: str = r'\[(\d+)\]',
        handle_amounts: bool = False
    ) -> pl.DataFrame:
        """Convert grouped columns into a long format DataFrame."""
        # Identify columns that belong to the repeating group
        grouped_cols = [col for col in df.columns if group_pattern in col]
        if not grouped_cols:
            raise ValueError(f"No columns found matching pattern: {group_pattern}")

        # Extract unique identifiers
        identifiers = self._extract_column_identifiers(
            grouped_cols, group_pattern, identifier_pattern
        )
        if not identifiers:
            raise ValueError(f"No valid identifiers found using pattern: {identifier_pattern}")

        # Set default base columns if not provided
        if base_cols is None:
            base_cols = [col for col in df.columns if group_pattern not in col]

        # Deduce attribute mappings if not provided
        if attribute_mappings is None:
            attribute_mappings = self._guess_attribute_mappings(grouped_cols, group_pattern)

        # Define output columns
        all_output_columns = base_cols + ['group_id'] + sorted(attribute_mappings.keys())

        long_dfs = []
        for id_num in sorted(identifiers, key=str):
            # Build select expressions for this group
            select_exprs = [pl.col(col) for col in base_cols]
            select_exprs.append(pl.lit(id_num).alias('group_id'))

            # Map attributes to columns
            for output_col, suffix_pattern in attribute_mappings.items():
                col_name = f'{group_pattern}[{id_num}]_{suffix_pattern}'
                if col_name in df.columns:
                    if handle_amounts and any(x in suffix_pattern for x in ['Amount', 'Amt']):
                        select_exprs.append(
                            pl.col(col_name)
                            .cast(pl.Utf8)
                            .str.replace(r'[^\d.-]', '')
                            .cast(pl.Float64)
                            .fill_null(0.0)
                            .alias(output_col)
                        )
                    else:
                        select_exprs.append(pl.col(col_name).alias(output_col))
                else:
                    # Fill with appropriate default value
                    if handle_amounts and any(x in suffix_pattern for x in ['Amount', 'Amt']):
                        select_exprs.append(pl.lit(0.0).cast(pl.Float64).alias(output_col))
                    else:
                        select_exprs.append(pl.lit(None).cast(pl.Utf8).alias(output_col))

            # Create DataFrame slice for this identifier
            group_df = df.select(select_exprs)
            
            # Filter empty rows
            group_df = self._filter_empty_rows(group_df, base_cols, handle_amounts)
            
            # Ensure consistent column order
            group_df = group_df.select(all_output_columns)
            long_dfs.append(group_df)

        # Combine and sort results
        if long_dfs:
            result = pl.concat(long_dfs)
            sort_cols = base_cols + ['group_id']
            return result

    def get_people(self) -> pl.DataFrame:
        """Extract and clean people information from Form 990 Core (Part VII).
        
        Returns:
            A Polars DataFrame containing people data with columns:
            - EIN, year, group_id
            - name, title, role_category, hours
            - is_trustee, is_officer, is_key_employee, is_highest_comp, is_former
            - comp_org, comp_related, other_comp, total_compensation
        """
        column_mappings = {
            'hours': 'AverageHoursPerWeekRt',
            'is_former': 'FormerOfcrDirectorTrusteeInd',
            'is_highest_comp': 'HighestCompensatedEmployeeInd',
            'is_trustee': 'IndividualTrusteeOrDirectorInd',
            'is_key_employee': 'KeyEmployeeInd',
            'is_officer': 'OfficerInd',
            'other_comp': 'OtherCompensationAmt',
            'name': 'PersonNm',
            'comp_org': 'ReportableCompFromOrgAmt',
            'comp_related': 'ReportableCompFromRltdOrgAmt',
            'title': 'TitleTxt'
        }

        people_df = self.create_long_format_df(
            df=self.core_df,
            group_pattern='Form990PartVIISectionAGrp',
            base_cols=['EIN', 'year'],
            attribute_mappings=column_mappings,
            handle_amounts=True
        )

        # Helper function for safer boolean conversion
        def safe_to_bool(s: pl.Series) -> pl.Series:
            return s.map_elements(
                lambda x: x == 'X' if isinstance(x, str) else bool(x),
                return_dtype=pl.Boolean
            ).fill_null(False)

        # Helper function for safer numeric conversion
        def safe_to_float(s: pl.Series) -> pl.Series:
            return (
                s.cast(pl.Utf8)
                .str.replace(r'[^\d.-]', '')
                .str.strip_chars()  # Using correct Polars method
                .map_elements(lambda x: float(x) if x else 0.0, return_dtype=pl.Float64)
                .fill_null(0.0)
            )

        result = (
            people_df
            # Cast numeric fields safely
            .with_columns([
                safe_to_float(pl.col('hours')).alias('hours')
            ])
            # Handle boolean columns safely
            .with_columns([
                *[
                    safe_to_bool(pl.col(col)).alias(col)
                    for col in [
                        'is_former', 'is_highest_comp', 'is_trustee',
                        'is_key_employee', 'is_officer'
                    ]
                ]
            ])
            # Clean text fields
            .with_columns([
                pl.col(['name', 'title'])
                .str.strip_chars()
                .str.replace(r'\s+', ' ')
                .str.to_titlecase()
            ])
            # Handle compensation amounts safely
            .with_columns([
                *[
                    safe_to_float(pl.col(col)).alias(col)
                    for col in ['comp_org', 'comp_related', 'other_comp']
                ]
            ])
            # Calculate total compensation
            .with_columns([
                (
                    pl.col('comp_org') 
                    + pl.col('comp_related') 
                    + pl.col('other_comp')
                ).alias('total_compensation')
            ])
            # Assign role category
            .with_columns([
                pl.when(pl.col('is_trustee')).then(pl.lit('Trustee/Director'))
                .when(pl.col('is_officer')).then(pl.lit('Officer'))
                .when(pl.col('is_key_employee')).then(pl.lit('Key Employee'))
                .when(pl.col('is_highest_comp')).then(pl.lit('Highest Compensated'))
                .when(pl.col('is_former')).then(pl.lit('Former'))
                .otherwise(pl.lit('Other'))
                .alias('role_category')
            ])
            # Sort and select final columns
            .sort(['year', 'total_compensation'], descending=[True, True])
            .select([
                'EIN', 'year', 'group_id',
                'name', 'title', 'role_category', 'hours',
                'is_trustee', 'is_officer', 'is_key_employee',
                'is_highest_comp', 'is_former',
                'comp_org', 'comp_related', 'other_comp',
                'total_compensation'
            ])
        )

        return result

    def get_investment_other_securities(self) -> pl.DataFrame:
        """Extract and clean 'other securities' information from Schedule D.

        Returns:
            A Polars DataFrame containing other securities data with columns:
            - EIN, year, group_id
            - description, book_value, valuation_method
        """
        attribute_mappings = {
            'description': 'Desc',
            'book_value': 'BookValueAmt',
            'valuation_method': 'MethodValuationCd'
        }

        long_df = self.create_long_format_df(
            df=self.schedule_d_df,
            group_pattern='OtherSecuritiesGrp',
            base_cols=['EIN', 'year'],
            attribute_mappings=attribute_mappings,
            handle_amounts=True
        )

        # Clean text columns and remove rows with no meaningful data
        return (
            long_df
            .with_columns(
                [
                    # Clean text data
                    pl.col(['description', 'valuation_method'])
                    .str.strip_chars()
                    .str.replace_all(r'\s+', ' ')
                    .str.to_titlecase(),
                    # Ensure book_value is numeric
                    pl.col('book_value')
                    .cast(pl.Utf8)
                    .str.replace(r'[^\d.-]', '')
                    .cast(pl.Float64)
                    .fill_null(0)
                ]
            )
            .filter(
                (pl.col('book_value') > 0)
                | pl.col('description').is_not_null()
                | pl.col('valuation_method').is_not_null()
            )
            .sort(['year', 'book_value'], descending=[False, True])
            .select([
                'EIN', 'year', 'description', 'book_value',
                'valuation_method', 'group_id'
            ])
        )

    def get_profile(self) -> pl.DataFrame:
        """Extract and clean organization profile information.
        
        Returns:
            A Polars DataFrame containing profile data with columns:
            - EIN, year, Filing_Date
            - Business name and DBA
            - Address information
            - Formation year, website
            - Officer/executive information
            - Mission/activity descriptions
            - Preparer information
        """
        # Define required columns
        profile_cols_core = [
            "EIN", "year",
            "PrincipalOfficerNm",
            "DoingBusinessAsName_BusinessNameLine1Txt",
            "USAddress_AddressLine1Txt", "USAddress_CityNm",
            "USAddress_StateAbbreviationCd", "USAddress_ZIPCd",
            "ActivityOrMissionDesc", "Desc", "MissionDesc",
            "WebsiteAddressTxt", "FormationYr",
            "TotalEmployeeCnt"
        ]

        profile_cols_header = [
            "EIN", "year", 
            "Filer_BusinessName_BusinessNameLine1Txt", "Filer_BusinessNameControlTxt",
            "ReturnTs", "PreparerFirmGrp_PreparerFirmEIN",
            "PreparerFirmGrp_PreparerFirmName_BusinessNameLine1Txt",
            "PreparerFirmGrp_PreparerUSAddress_AddressLine1Txt",
            "PreparerFirmGrp_PreparerUSAddress_StateAbbreviationCd",
            "PreparerFirmGrp_PreparerUSAddress_ZIPCd",
            "PreparerPersonGrp_PreparerPersonNm",
            "BusinessOfficerGrp_PersonNm", "BusinessOfficerGrp_PersonTitleTxt",
            "BusinessOfficerGrp_PhoneNum"
        ]

        # Get available columns
        available_core_cols = [col for col in profile_cols_core if col in self.core_df.columns]
        available_header_cols = [col for col in profile_cols_header if col in self.return_header_df.columns]

        # Join core and header data
        profile_df = (
            self.core_df.select(available_core_cols)
            .join(
                self.return_header_df.select(available_header_cols),
                on=["EIN", "year"],
                how="left"
            )
        )

        # Helper function for safe column operations
        def safe_cols(df: pl.DataFrame, cols: list[str]) -> list[str]:
            """Return only columns that exist in the DataFrame."""
            return [col for col in cols if col in df.columns]

        # Helper function for safe string concatenation
        def safe_concat_address(df: pl.DataFrame, cols: list[str], separator: str = ', ') -> pl.Expr:
            """Safely concatenate address fields."""
            existing_cols = [col for col in cols if col in df.columns]
            if not existing_cols:
                return pl.lit(None)
            return pl.concat_str(pl.col(existing_cols), separator=separator)

        # Transform the data
        result = profile_df

        # Combine officer information if columns exist
        officer_cols = safe_cols(profile_df, ["PrincipalOfficerNm", "BusinessOfficerGrp_PersonNm"])
        if len(officer_cols) > 0:
            result = result.with_columns([
                pl.coalesce(
                    *[pl.col(col) for col in officer_cols]
                ).alias("officer_name")
            ])

        # Clean text fields that exist
        text_cols = safe_cols(result, [
            'officer_name',
            'DoingBusinessAsName_BusinessNameLine1Txt',
            'Filer_BusinessName_BusinessNameLine1Txt',
            'PreparerPersonGrp_PreparerPersonNm',
            'BusinessOfficerGrp_PersonTitleTxt',
            'ActivityOrMissionDesc', 'Desc', 'MissionDesc'
        ])
        if text_cols:
            result = result.with_columns([
                pl.col(text_cols).str.to_titlecase()
            ])

        # Format filing date if it exists
        if "ReturnTs" in result.columns:
            result = result.with_columns([
                pl.col('ReturnTs').str.slice(0, 10).alias('Filing_Date')
            ])

        # Combine addresses
        result = result.with_columns([
            safe_concat_address(
                result,
                [
                    'USAddress_AddressLine1Txt',
                    'USAddress_CityNm',
                    'USAddress_StateAbbreviationCd',
                    'USAddress_ZIPCd'
                ]
            ).alias('FullAddress'),
            safe_concat_address(
                result,
                [
                    'PreparerFirmGrp_PreparerUSAddress_AddressLine1Txt',
                    'PreparerFirmGrp_PreparerUSAddress_StateAbbreviationCd',
                    'PreparerFirmGrp_PreparerUSAddress_ZIPCd'
                ]
            ).alias('PreparerFirmAddress')
        ])

        # Clean up addresses if they exist
        address_cols = safe_cols(result, ['FullAddress', 'PreparerFirmAddress'])
        if address_cols:
            result = result.with_columns([
                pl.col(address_cols).str.to_titlecase()
            ])

        # Define desired final columns
        final_cols = [
            'EIN', 'year', 'Filing_Date',
            'DoingBusinessAsName_BusinessNameLine1Txt',
            'Filer_BusinessName_BusinessNameLine1Txt',
            'Filer_BusinessNameControlTxt',
            'FormationYr', 'WebsiteAddressTxt', 
            'FullAddress', 'TotalEmployeeCnt',
            'ActivityOrMissionDesc', 'Desc', 'MissionDesc',
            'officer_name', 'BusinessOfficerGrp_PersonTitleTxt',
            'BusinessOfficerGrp_PhoneNum',
            'PreparerFirmGrp_PreparerFirmName_BusinessNameLine1Txt',
            'PreparerFirmGrp_PreparerFirmEIN', 'PreparerFirmAddress',
            'PreparerPersonGrp_PreparerPersonNm'
        ]

        # Select only columns that exist
        available_final_cols = [col for col in final_cols if col in result.columns]
        result = result.select(available_final_cols).sort('year', descending=True)

        return result

    def get_contractors(self) -> pl.DataFrame:
        """Extract and clean contractor information from Form 990 Core.
        
        Returns:
            A Polars DataFrame containing contractor data with columns:
            - EIN, year, documentId, group_id
            - contractor_name: Name of the contracting business
            - full_address: Combined address information
            - services: Description of services provided
            - compensation: Amount paid to contractor
        """
        attribute_mappings = {
            'contractor_name': 'ContractorName_BusinessName_BusinessNameLine1Txt',
            'address_line': 'ContractorAddress_USAddress_AddressLine1Txt',
            'city': 'ContractorAddress_USAddress_CityNm',
            'state': 'ContractorAddress_USAddress_StateAbbreviationCd',
            'zip': 'ContractorAddress_USAddress_ZIPCd',
            'services': 'ServicesDesc',
            'compensation': 'CompensationAmt'
        }

        contractors_df = self.create_long_format_df(
            df=self.core_df,
            group_pattern='ContractorCompensationGrp',
            base_cols=['EIN', 'year', 'documentId'],
            attribute_mappings=attribute_mappings,
            handle_amounts=True
        )

        # If no data was found, return empty DataFrame with correct schema
        if contractors_df.height == 0:
            schema = {
                'EIN': pl.Utf8,
                'year': pl.Int32,
                'documentId': pl.Utf8,
                'group_id': pl.Utf8,
                'contractor_name': pl.Utf8,
                'full_address': pl.Utf8,
                'services': pl.Utf8,
                'compensation': pl.Float64
            }
            return pl.DataFrame(schema=schema)

        result = (
            contractors_df
            # Clean text fields
            .with_columns([
                pl.col(['contractor_name', 'address_line', 'city', 'services'])
                .str.strip_chars()
                .str.replace(r'\s+', ' ')
                .str.to_titlecase()
            ])
            # Combine address components safely
            .with_columns([
                pl.concat_str(
                    [
                        pl.col(col) for col in ['address_line', 'city', 'state', 'zip']
                        if col in contractors_df.columns
                    ],
                    separator=', '
                ).alias('full_address')
            ])
            # Ensure compensation is numeric
            .with_columns([
                pl.col('compensation')
                .cast(pl.Float64)
                .fill_null(0.0)
            ])
            # Remove rows with no meaningful data
            .filter(
                (pl.col('compensation') > 0) 
                | pl.col('contractor_name').is_not_null()
            )
            # Sort by year and compensation
            .sort(['year', 'compensation'], descending=[True, True])
            # Select final columns
            .select([
                'EIN', 'year', 'documentId', 'group_id',
                'contractor_name', 'full_address', 'services',
                'compensation'
            ])
        )

        return result

    def _guess_attribute_mappings(
        self,
        grouped_columns: list[str],
        group_pattern: str
    ) -> Dict[str, str]:
        """Guess attribute mappings from column names."""
        attr_names = set()
        for col_name in grouped_columns:
            parts = col_name.split('__')
            if len(parts) > 1:
                attr_name = parts[-1]
            else:
                pattern_parts = col_name.split(group_pattern)
                if len(pattern_parts) > 1 and '_' in pattern_parts[1]:
                    _, maybe_suffix = pattern_parts[1].split('_', 1)
                    attr_name = maybe_suffix
                else:
                    continue
            attr_names.add(attr_name)

        return {name: name for name in attr_names}

    def _filter_empty_rows(
        self,
        df_slice: pl.DataFrame,
        base_cols: list[str],
        handle_amounts: bool
    ) -> pl.DataFrame:
        """Filter out empty or zero-value rows with better type handling."""
        if handle_amounts:
            amount_cols = [
                col for col in df_slice.columns
                if col not in base_cols and 'group_id' not in col
                and any(x in col.lower() for x in ['amt', 'amount', 'comp', 'salary', 'bonus'])
            ]
            if amount_cols:
                # Clean numeric columns more safely
                df_slice = df_slice.with_columns([
                    pl.col(col)
                    .cast(pl.Utf8)
                    .str.replace(r'[^\d.-]', '')
                    .str.strip_chars()  # Using correct Polars method
                    .map_elements(lambda x: float(x) if x else 0.0, return_dtype=pl.Float64)
                    .fill_null(0.0)
                    .alias(col)
                    for col in amount_cols
                ])
                # Keep rows where at least one numeric column is > 0
                df_slice = df_slice.filter(
                    pl.any_horizontal([pl.col(col) > 0 for col in amount_cols])
                )
        else:
            # Filter non-amount data
            value_cols = [c for c in df_slice.columns if c not in base_cols and c != 'group_id']
            if value_cols:
                df_slice = df_slice.filter(
                    pl.any_horizontal([pl.col(col).is_not_null() for col in value_cols])
                )

        return df_slice

    def get_compensation_data(self) -> pl.DataFrame:
        """Extract and format compensation data from Schedule J.
        
        Returns:
            A Polars DataFrame containing compensation data with columns:
            - EIN, year, documentId, group_id
            - person_name, title, base_compensation, bonus,
              deferred_compensation, nontaxable_benefits,
              other_compensation, total_compensation
        """
        comp_mappings = {
            "person_name": "PersonNm",
            "title": "TitleTxt",
            "base_compensation": "BaseCompensationFilingOrgAmt",
            "bonus": "BonusFilingOrganizationAmount",
            "other_compensation": "OtherCompensationFilingOrgAmt",
            "deferred_compensation": "DeferredCompensationFlngOrgAmt",
            "nontaxable_benefits": "NontaxableBenefitsFilingOrgAmt",
            "total_compensation": "TotalCompensationFilingOrgAmt"
        }

        comp_df = self.create_long_format_df(
            df=self.schedule_j_df,
            group_pattern="RltdOrgOfficerTrstKeyEmplGrp",
            base_cols=["EIN", "year", "documentId"],
            attribute_mappings=comp_mappings,
            handle_amounts=True
        )

        # Clean and finalize the compensation data
        result = (
            comp_df
            .with_columns([
                # Clean text fields
                pl.col(['person_name', 'title'])
                .str.strip_chars()
                .str.replace_all(r'\s+', ' ')
                .str.to_titlecase()
            ])
            .with_columns([
                # Ensure numeric columns are properly cast and nulls are zero
                pl.col([
                    'base_compensation',
                    'bonus',
                    'deferred_compensation',
                    'nontaxable_benefits',
                    'other_compensation'
                ]).cast(pl.Float64).fill_null(0)
            ])
            .with_columns([
                # Recalculate total_compensation if any partial data changed
                (
                    pl.col('base_compensation')
                    + pl.col('bonus')
                    + pl.col('deferred_compensation')
                    + pl.col('nontaxable_benefits')
                    + pl.col('other_compensation')
                ).alias('total_compensation')
            ])
            .sort(['year', 'total_compensation'], descending=[False, True])
            .select([
                'EIN', 'year', 'documentId', 'group_id',
                'person_name', 'title',
                'base_compensation', 'bonus', 'deferred_compensation',
                'nontaxable_benefits', 'other_compensation',
                'total_compensation'
            ])
        )
        return result

    def get_revenue_expense(self) -> pl.DataFrame:
        """Extract revenue and expense information from Form 990 Core.

        Returns:
            A Polars DataFrame containing revenue and expense data with columns:
            - EIN, year
            - total_revenue, contributions, investment_income,
              total_expenses, grants, salaries, investment_fees
        """
        column_mappings = {
            'CYTotalRevenueAmt': 'total_revenue',
            'CYContributionsGrantsAmt': 'contributions',
            'CYInvestmentIncomeAmt': 'investment_income',
            'CYTotalExpensesAmt': 'total_expenses',
            'GrantAmt': 'grants',
            'CYSalariesCompEmpBnftPaidAmt': 'salaries',
            'FeesForSrvcInvstMgmntFeesGrp_TotalAmt': 'investment_fees'
        }

        # Select columns, rename, and clean numeric data
        return (
            self.core_df
            .select(['EIN', 'year'] + list(column_mappings.keys()))
            .rename(column_mappings)
            .drop_nulls('total_revenue')  # ensures we only keep rows with revenue data
            .with_columns([
                pl.col([
                    'total_revenue', 'contributions', 'investment_income',
                    'total_expenses', 'grants', 'salaries', 'investment_fees'
                ]).cast(pl.Float64).fill_null(0)
            ])
            .sort('year', descending=True)
        )

    def get_endowment(self) -> pl.DataFrame:
        """Extract endowment information from Schedule D.

        Returns:
            A Polars DataFrame containing endowment data with columns:
            - EIN, year
            - beginning_balance, contributions, investment_earnings,
            other_expenditures, end_balance,
            - board_designated_pct, permanent_endowment_pct, term_endowment_pct
        """
        # Define all possible column mappings
        column_mappings = {
            # Try different possible column names for each field
            'beginning_balance': [
                'CYEndwmtFundGrp_BeginningYearBalanceAmt',
                'EndowmentBalanceGrp_BeginningYearBalanceAmt',
                'BeginningYearBalanceAmt'
            ],
            'contributions': [
                'CYEndwmtFundGrp_ContributionsAmt',
                'EndowmentBalanceGrp_ContributionsAmt',
                'ContributionsAmt'
            ],
            'investment_earnings': [
                'CYEndwmtFundGrp_InvestmentEarningsOrLossesAmt',
                'EndowmentBalanceGrp_InvestmentEarningsOrLossesAmt',
                'InvestmentEarningsOrLossesAmt'
            ],
            'other_expenditures': [
                'CYEndwmtFundGrp_OtherExpendituresAmt',
                'EndowmentBalanceGrp_OtherExpendituresAmt',
                'OtherExpendituresAmt'
            ],
            'end_balance': [
                'CYEndwmtFundGrp_EndYearBalanceAmt',
                'EndowmentBalanceGrp_EndYearBalanceAmt',
                'EndYearBalanceAmt'
            ],
            'board_designated_pct': [
                'BoardDesignatedBalanceEOYPct',
                'BoardDesignatedEndowmentBalancePct'
            ],
            'permanent_endowment_pct': [
                'PrmnntEndowmentBalanceEOYPct',
                'PermanentEndowmentBalancePct'
            ],
            'term_endowment_pct': [
                'TermEndowmentBalanceEOYPct',
                'TermEndowmentBalancePct'
            ]
        }

        # Find available columns for each field
        available_columns = {}
        for field, possible_cols in column_mappings.items():
            for col in possible_cols:
                if col in self.schedule_d_df.columns:
                    available_columns[field] = col
                    break
            if field not in available_columns:
                # If no matching column found, we'll create it with nulls
                available_columns[field] = pl.lit(None).alias(field)

        # Create base selection with required columns
        select_exprs = [pl.col('EIN'), pl.col('year')]
        
        # Add available columns or null placeholders
        for field, col_expr in available_columns.items():
            if isinstance(col_expr, str):
                # It's an existing column
                select_exprs.append(pl.col(col_expr).alias(field))
            else:
                # It's a null placeholder expression
                select_exprs.append(col_expr)

        # Process the data
        result = (
            self.schedule_d_df
            .select(select_exprs)
            .with_columns([
                # Convert amount columns to float and handle nulls
                pl.col([
                    'beginning_balance', 'contributions', 'investment_earnings',
                    'other_expenditures', 'end_balance'
                ]).cast(pl.Float64).fill_null(0.0),
                # Convert percentage columns to float and handle nulls
                pl.col([
                    'board_designated_pct', 'permanent_endowment_pct',
                    'term_endowment_pct'
                ]).cast(pl.Float64).fill_null(0.0)
            ])
            # Remove rows where all amount fields are zero
            .filter(
                (pl.col('beginning_balance') != 0) |
                (pl.col('contributions') != 0) |
                (pl.col('investment_earnings') != 0) |
                (pl.col('other_expenditures') != 0) |
                (pl.col('end_balance') != 0)
            )
            .sort('year', descending=True)
        )

        if result.height == 0:
            # Return empty DataFrame with correct schema if no data
            schema = {
                'EIN': pl.Utf8,
                'year': pl.Int32,
                'beginning_balance': pl.Float64,
                'contributions': pl.Float64,
                'investment_earnings': pl.Float64,
                'other_expenditures': pl.Float64,
                'end_balance': pl.Float64,
                'board_designated_pct': pl.Float64,
                'permanent_endowment_pct': pl.Float64,
                'term_endowment_pct': pl.Float64
            }
            return pl.DataFrame(schema=schema)

        return result

    def get_invested(self) -> pl.DataFrame:
        """Extract and analyze investment balances across different categories.
        
        Returns:
            A Polars DataFrame containing investment data with columns:
            - EIN, year
            - public_securities_{boy/eoy}: Beginning/end of year public securities
            - other_securities_{boy/eoy}: Beginning/end of year other securities
            - cash_and_savings_{boy/eoy}: Beginning/end of year cash/savings
            - total_investments_{boy/eoy}: Total beginning/end of year investments
            - net_investment_change: Change in total investments over the year
            - *_pct: Percentage of total for each category
        """
        column_mappings = {
            'InvestmentsPubTradedSecGrp_BOYAmt': 'public_securities_boy',
            'InvestmentsPubTradedSecGrp_EOYAmt': 'public_securities_eoy',
            'InvestmentsOtherSecuritiesGrp_BOYAmt': 'other_securities_boy',
            'InvestmentsOtherSecuritiesGrp_EOYAmt': 'other_securities_eoy',
            'SavingsAndTempCashInvstGrp_BOYAmt': 'cash_and_savings_boy',
            'SavingsAndTempCashInvstGrp_EOYAmt': 'cash_and_savings_eoy'
        }

        # Select and rename columns
        investment_df = (
            self.core_df
            .select(['EIN', 'year'] + list(column_mappings.keys()))
            .rename(column_mappings)
        )

        # Clean numeric columns
        result = (
            investment_df
            .with_columns([
                pl.col([
                    'public_securities_boy', 'public_securities_eoy',
                    'other_securities_boy', 'other_securities_eoy',
                    'cash_and_savings_boy', 'cash_and_savings_eoy'
                ]).cast(pl.Float64).fill_null(0.0)
            ])
            .with_columns([
                # Calculate totals
                (
                    pl.col('public_securities_boy')
                    + pl.col('other_securities_boy')
                    + pl.col('cash_and_savings_boy')
                ).alias('total_investments_boy'),
                (
                    pl.col('public_securities_eoy')
                    + pl.col('other_securities_eoy')
                    + pl.col('cash_and_savings_eoy')
                ).alias('total_investments_eoy'),
            ])
            .with_columns([
                # Calculate net change
                (
                    pl.col('total_investments_eoy')
                    - pl.col('total_investments_boy')
                ).alias('net_investment_change'),
                
                # Calculate percentages
                (
                    pl.when(pl.col('total_investments_eoy') > 0)
                    .then(pl.col('public_securities_eoy') / pl.col('total_investments_eoy') * 100)
                    .otherwise(0.0)
                ).round(2).alias('public_securities_pct'),
                
                (
                    pl.when(pl.col('total_investments_eoy') > 0)
                    .then(pl.col('other_securities_eoy') / pl.col('total_investments_eoy') * 100)
                    .otherwise(0.0)
                ).round(2).alias('other_securities_pct'),
                
                (
                    pl.when(pl.col('total_investments_eoy') > 0)
                    .then(pl.col('cash_and_savings_eoy') / pl.col('total_investments_eoy') * 100)
                    .otherwise(0.0)
                ).round(2).alias('cash_and_savings_pct')
            ])
            .sort('year', descending=True)
        )
        
        return result
    
# def main():
#     """Example usage of the Multi_IRS990_Forms class."""
#     # Configure Polars display settings (optional)
#     # pl.Config.set_tbl_cols(20).set_tbl_rows(100).set_fmt_str_lengths(150)

#     try:
#         forms = Multi_IRS990_Forms('237172306')

#         print("\nCompensation DataFrame:")
#         print(forms.get_compensation_data())

#         print("\nRevenue and Expense DataFrame:")
#         print(forms.get_revenue_expense())

#         print("\nEndowment DataFrame:")
#         print(forms.get_endowment())

#         print("\nSecurities DataFrame:")
#         print(forms.get_investment_other_securities())

#         print("\nPeople DataFrame:")
#         print(forms.get_people())

#         print("\nProfile DataFrame:")
#         print(forms.get_profile())

#         print("\nProfile DataFrame:")
#         print(forms.get_invested())

#         print("\nProfile DataFrame:")
#         print(forms.get_contractors())

#     except Exception as e:
#         print(f"Error processing IRS 990 forms: {str(e)}")
#     # finally:
#     #     pl.Config.restore_defaults()

# if __name__ == "__main__":
#     main()

# ---------------------------------------------------------------------------- #
#                                    Testing                                   #
# ---------------------------------------------------------------------------- #

# from nonprofit_builder import Form990Processor
# import polars as pl

# ["237172306", "362722198", "042111203"]

# EIN = "362722198"
# long_processor = Form990Processor()
# abc_df = long_processor.run(EIN)
# forms_new = Multi_IRS990_Forms(EIN, abc_df)

# # forms_new.get_compensation_data()
# # forms_new.get_invested()
# # forms_new.get_investment_other_securities()
# # forms_new.get_revenue_expense()
# # forms_new.get_profile()
# # forms_new.get_people()
# # forms_new.get_contractors()
# # forms_new.get_endowment()


# def print_all_summaries(forms_obj):
#     """Print summaries of all available DataFrames from a Multi_IRS990_Forms object."""
    
#     # Define all methods to call with their display names
#     methods = {
#         'Compensation Data': forms_obj.get_compensation_data,
#         'Investment Holdings': forms_obj.get_invested,
#         'Other Securities': forms_obj.get_investment_other_securities,
#         'Revenue & Expenses': forms_obj.get_revenue_expense,
#         'Organization Profile': forms_obj.get_profile,
#         'People': forms_obj.get_people,
#         'Contractors': forms_obj.get_contractors,
#         'Endowment': forms_obj.get_endowment
#     }
    
#     results = {}
#     errors = {}
    
#     # Try to get each DataFrame
#     for name, method in methods.items():
#         try:
#             df = method()
#             results[name] = df
#         except Exception as e:
#             errors[name] = str(e)
    
#     # Print results
#     print(f"\n{'='*80}")
#     print(f"Summary for EIN: {forms_obj.ein}")
#     print(f"{'='*80}\n")
    
#     for name, df in results.items():
#         print(f"\n{'-'*40}")
#         print(f"{name}:")
#         print(f"{'-'*40}")
        
#         if df.height == 0:
#             print("No data available")
#         else:
#             print(f"Rows: {df.height}")
#             print(f"Columns: {df.width}")
#             print("\nColumns:")
#             for col in df.columns:
#                 print(f"- {col}")
#             print("\nSample Data:")
#             print(df.head(3))
        
#         print("\n")
    
#     # Print any errors that occurred
#     if errors:
#         print(f"\n{'='*40}")
#         print("Errors encountered:")
#         print(f"{'='*40}")
#         for name, error in errors.items():
#             print(f"\n{name}:")
#             print(f"Error: {error}")

# # Usage example:
# print_all_summaries(forms_new)
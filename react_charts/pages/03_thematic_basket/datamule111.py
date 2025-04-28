from datamule import Portfolio

# Create a Portfolio object
portfolio = Portfolio('output_dir') # can be an existing directory or a new one

# Download submissions
portfolio.download_submissions(
   filing_date=('2023-01-01','2023-01-03'),
   submission_type=['10-K']
)

# Iterate through documents by document type
for ten_k in portfolio.document_type('10-K'):
   ten_k.parse()
   print(ten_k.data['document']['part2']['item7'])

# Iterate through documents by what strings they contain
for document in portfolio.contains_string('United States'):
   print(document.path)

# You can also use regex patterns
for document in portfolio.contains_string(r'(?i)covid-19'):
   print(document.type)

# For faster operations, you can take advantage of built in threading with callback function
def callback(submission):
   print(submission.path)

submission_results = portfolio.process_submissions(callback)
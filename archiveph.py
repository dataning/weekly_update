import datetime
import time
import requests
import pandas as pd
from rich import pretty
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.console import Console

# Initialize Rich console for prettier output
pretty.install()
console = Console()

token = 'YvvyUyAud3ubAS2HrhhjYmMUSrShcYgq6znWuaoCmR60jOwrLfFrKlMdP0xPXkl102QjDqbOVJO04wr5fwEH1ZwNjepLQ0ew1YOzuI0Tn1Wo1eQwjEGn8baIgLJmauXm6caxjQhsYyNhefWw51TP75S8h1GicyCMMPodGXSOhwuKdOpf4nKLYjNHF6CaQVkMPImqcuE0'

def convert_export_to_df(export_data):
    """
    Convert Readwise Reader API v3/list data to DataFrame
    """
    if not export_data:
        return pd.DataFrame()
    
    # Each item is already a flat document, so we can convert directly to DataFrame
    df = pd.DataFrame(export_data)
    
    # Process tags if needed (they appear to be objects in your data)
    if 'tags' in df.columns:
        # Convert tag objects to a list of tag names
        df['tag_names'] = df['tags'].apply(lambda x: list(x.keys()) if isinstance(x, dict) else [])
    
    # Convert date columns to datetime
    date_columns = ['created_at', 'updated_at', 'first_opened_at', 'last_opened_at', 
                    'saved_at', 'last_moved_at', 'published_date']
    
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='ignore')
    
    return df

def fetch_reader_document_list_api(updated_after=None, with_html_content=False, location=None):
    """
    Fetch documents from Readwise Reader API
    
    Args:
        updated_after: ISO format datetime string - only fetch documents updated after this time
        with_html_content: If True, include the full HTML content of documents
        location: Filter by document location (e.g., 'archive')
        
    Returns:
        List of document data from the API
    """
    full_data = []
    next_page_cursor = None
    page_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TimeElapsedColumn()
    ) as progress:
        task = progress.add_task("[green]Fetching documents from Readwise...", total=None)
        
        while True:
            params = {}
            if next_page_cursor:
                params['pageCursor'] = next_page_cursor
            if updated_after:
                params['updatedAfter'] = updated_after
            if with_html_content:
                params['withHtmlContent'] = 'true'
            if location:
                params['location'] = location
                
            page_count += 1
            progress.update(task, description=f"[green]Fetching page {page_count} from Readwise...")
            
            try:
                response = requests.get(
                    url="https://readwise.io/api/v3/list/",
                    params=params,
                    headers={"Authorization": f"Token {token}"}
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    progress.update(task, description=f"[yellow]Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                
                # Handle other errors
                response.raise_for_status()
                
                json_response = response.json()
                results = json_response.get('results', [])
                full_data.extend(results)
                
                progress.update(task, description=f"[green]Fetched page {page_count} with {len(results)} documents")
                
                next_page_cursor = json_response.get('nextPageCursor')
                if not next_page_cursor:
                    break
                
                # Small delay to be nice to the API
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                progress.update(task, description=f"[red]Error: {str(e)}")
                console.print(f"[bold red]Error during API request:[/] {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    console.print(f"Response status: {e.response.status_code}")
                    console.print(f"Response body: {e.response.text}")
                break
    
    console.print(f"[bold green]Completed fetching {len(full_data)} documents across {page_count} pages[/]")
    return full_data


console.print("[bold]Fetching all documents with HTML content...[/]")
all_data = fetch_reader_document_list_api(with_html_content=True)
df_all = convert_export_to_df(all_data)
df_all['html_content'].iloc[13]
df_all.head(50)

# Get recent documents (from the past day)
console.print("\n[bold]Fetching documents from the past day...[/]")
docs_after_date = datetime.datetime.now() - datetime.timedelta(days=1)
new_data = fetch_reader_document_list_api(
    updated_after=docs_after_date.isoformat(),
    with_html_content=True
)

new_data


# Use this new function instead
df_documents = convert_export_to_df(new_data); df_documents

new_df = convert_export_to_df(new_data)
console.print(f"[bold green]Found {len(new_df)} highlights from the past day")

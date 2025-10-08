# Gitlab MCP Server for Agents

## Overview
This is a Gitlab MCP Server specifically for Agents (eg: Pydantic AI). This was developed due to incompatibility of the various other gitlab mcp servers , including the official one with pydantic & llms like google-gemini. 
This is a wrapper around [gitlab-mcp](https://github.com/zereight/gitlab-mcp) & provides access to all of the tools present (62 !)

## Key Features

- **Compatible**: Compatible with the latest frameworks & tools like pydantic , google-gemini . 
- **Extensive Toolset**: Access a wide range of tools for CRUD operations on Merge requests, files, repositories, branches, notes, issues, namespaces, projects ,labels, commits, events.
- **Validation**: Improved validation for Tool inputs, properties & JSON schemas.
---
## Project Structure
```
.
├── server.py  # wrapper class around @zereight/mcp-gitlab to manage it's runtime, async context, list & call tools.  
├── server2.py # low level mcp server re-packaging the modified tools.
├── requirements.txt # Python package requirements
├── utils.py # Code for replacing references in the json tool input schema with the actual attributes.
├── utils2.py # Code for further modifying the tool input schema (remove nested dicts, arrays, other not supported keys).
├── app.py # Example code for how to run the mcp server with a pydantic ai agent.
└── README.md  # This file
```

## Usage

### Local usage

1. Clone the repository:
   ```bash
   git clone https://github.com/eshan1347/gitlab-agent-mcp.git
   cd gitlab-agent-mcp
2. Install requirements :
   ```bash
   pip install -r requirements.txt
3. Run the mcp server :
   ```python
   server = pydantic_ai.mcp.MCPServerStdio(
    command='python',
    args=[
        'server2.py'
    ],
    env={
        'GITLAB_ACCESS_TOKEN': "your_gitlab_token",
        'GITLAB_PROJECT_ID': "your_project_id" //Optional        
    }
     )

### Environment Variables : 
1. `GITLAB_PERSONAL_ACCESS_TOKEN`: Your GitLab personal access token.
2. `GITLAB_API_URL`: Your GitLab API URL. (Default: https://gitlab.com/api/v4)
3. `GITLAB_PROJECT_ID`: Default project ID. If set, Overwrite this value when making an API request.
4. `GITLAB_ALLOWED_PROJECT_IDS`: Optional comma-separated list of allowed project IDs. When set with a single value, acts as a default project (like the old "lock" mode). When set with multiple values, restricts access to only those projects.
5. `Single` value 123: MCP server can only access project 123 and uses it as default
6. `Multiple` values 123,456,789: MCP server can access projects 123, 456, and 789 but requires explicit project ID in requests
7. `GITLAB_READ_ONLY_MODE`: When set to 'true', restricts the server to only expose read-only operations. Useful for enhanced security or when write access is not needed. Also useful for using with Cursor and it's 40 tool limit.
8. `GITLAB_DENIED_TOOLS_REGEX`: When set as a regular expression, it excludes the matching tools.
9. `USE_GITLAB_WIKI`: When set to 'true', enables the wiki-related tools (list_wiki_pages, get_wiki_page, create_wiki_page, update_wiki_page, delete_wiki_page). By default, wiki features are disabled.
10. `USE_MILESTONE`: When set to 'true', enables the milestone-related tools (list_milestones, get_milestone, create_milestone, edit_milestone, delete_milestone, get_milestone_issue, get_milestone_merge_requests, promote_milestone, get_milestone_burndown_events). By default, milestone features are disabled.
11. `USE_PIPELINE`: When set to 'true', enables the pipeline-related tools (list_pipelines, get_pipeline, list_pipeline_jobs, list_pipeline_trigger_jobs, get_pipeline_job, get_pipeline_job_output, create_pipeline, retry_pipeline, cancel_pipeline, play_pipeline_job, retry_pipeline_job, cancel_pipeline_job). By default, pipeline features are disabled.
12. `GITLAB_AUTH_COOKIE_PATH`: Path to an authentication cookie file for GitLab instances that require cookie-based authentication. When provided, the cookie will be included in all GitLab API requests.
13. `GITLAB_COMMIT_FILES_PER_PAGE`: The number of files per page that GitLab returns for commit diffs. This value should match the server-side GitLab setting. Adjust this if your GitLab instance uses a custom per-page value for commit diffs.

## Tools  :
- `merge_merge_request` - Merge a merge request in a GitLab project
- `create_or_update_file` - Create or update a single file in a GitLab project
- `search_repositories` - Search for GitLab projects
- `create_repository` - Create a new GitLab project
- `get_file_contents` - Get the contents of a file or directory from a GitLab project
- `push_files` - Push multiple files to a GitLab project in a single commit
- `create_issue` - Create a new issue in a GitLab project
- `create_merge_request` - Create a new merge request in a GitLab project
- `fork_repository` - Fork a GitLab project to your account or specified namespace
- `create_branch` - Create a new branch in a GitLab project
- `get_merge_request` - Get details of a merge request (Either mergeRequestIid or branchName must be provided)
- `get_merge_request_diffs` - Get the changes/diffs of a merge request (Either mergeRequestIid or branchName must be provided)
- `list_merge_request_diffs` - List merge request diffs with pagination support (Either mergeRequestIid or branchName must be provided)
- `get_branch_diffs` - Get the changes/diffs between two branches or commits in a GitLab project
- `update_merge_request` - Update a merge request (Either mergeRequestIid or branchName must be provided)
- `create_note` - Create a new note (comment) to an issue or merge request
- `create_merge_request_thread` - Create a new thread on a merge request
- `mr_discussions` - List discussion items for a merge request
- `update_merge_request_note` - Modify an existing merge request thread note
- `create_merge_request_note` - Add a new note to an existing merge request thread
- `get_draft_note` - Get a single draft note from a merge request
- `list_draft_notes` - List draft notes for a merge request
- `create_draft_note` - Create a draft note for a merge request
- `update_draft_note` - Update an existing draft note
- `delete_draft_note` - Delete a draft note
- `publish_draft_note` - Publish a single draft note
- `bulk_publish_draft_notes` - Publish all draft notes for a merge request
- `update_issue_note` - Modify an existing issue thread note
- `create_issue_note` - Add a new note to an existing issue thread
- `list_issues` - List issues (default: created by current user only; use scope='all' for all accessible issues)
- `my_issues` - List issues assigned to the authenticated user (defaults to open issues)
- `get_issue` - Get details of a specific issue in a GitLab project
- `update_issue` - Update an issue in a GitLab project
- `delete_issue` - Delete an issue from a GitLab project
- `list_issue_links` - List all issue links for a specific issue
- `list_issue_discussions` - List discussions for an issue in a GitLab project
- `get_issue_link` - Get a specific issue link
- `create_issue_link` - Create an issue link between two issues
- `delete_issue_link` - Delete an issue link
- `list_namespaces` - List all namespaces available to the current user
- `get_namespace` - Get details of a namespace by ID or path
- `verify_namespace` - Verify if a namespace path exists
- `get_project` - Get details of a specific project
- `list_projects` - List projects accessible by the current user
- `list_project_members` - List members of a GitLab project
- `list_labels` - List labels for a project
- `get_label` - Get a single label from a project
- `create_label` - Create a new label in a project
- `update_label` - Update an existing label in a project
- `delete_label` - Delete a label from a project
- `list_group_projects` - List projects in a GitLab group with filtering options
- `list_wiki_pages` - List wiki pages in a GitLab project
- `get_wiki_page` - Get details of a specific wiki page
- `create_wiki_page` - Create a new wiki page in a GitLab project
- `update_wiki_page` - Update an existing wiki page in a GitLab project
- `delete_wiki_page` - Delete a wiki page from a GitLab project
- `get_repository_tree` - Get the repository tree for a GitLab project (list files and directories)
- `list_pipelines` - List pipelines in a GitLab project with filtering options
- `get_pipeline` - Get details of a specific pipeline in a GitLab project
- `list_pipeline_jobs` - List all jobs in a specific pipeline
- `list_pipeline_trigger_jobs` - List all trigger jobs (bridges) in a specific pipeline that trigger downstream pipelines
- `get_pipeline_job` - Get details of a GitLab pipeline job number
- `get_pipeline_job_output` - Get the output/trace of a GitLab pipeline job with optional pagination to limit context window usage
- `create_pipeline` - Create a new pipeline for a branch or tag
- `retry_pipeline` - Retry a failed or canceled pipeline
- `cancel_pipeline` - Cancel a running pipeline
- `play_pipeline_job` - Run a manual pipeline job
- `retry_pipeline_job` - Retry a failed or canceled pipeline job
- `cancel_pipeline_job` - Cancel a running pipeline job
- `list_merge_requests` - List merge requests in a GitLab project with filtering options
- `list_milestones` - List milestones in a GitLab project with filtering options
- `get_milestone` - Get details of a specific milestone
- `create_milestone` - Create a new milestone in a GitLab project
- `edit_milestone` - Edit an existing milestone in a GitLab project
- `delete_milestone` - Delete a milestone from a GitLab project
- `get_milestone_issue` - Get issues associated with a specific milestone
- `get_milestone_merge_requests` - Get merge requests associated with a specific milestone
- `promote_milestone` - Promote a milestone to the next stage
- `get_milestone_burndown_events` - Get burndown events for a specific milestone
- `get_users` - Get GitLab user details by usernames
- `list_commits` - List repository commits with filtering options
- `get_commit` - Get details of a specific commit
- `get_commit_diff` - Get changes/diffs of a specific commit
- `list_group_iterations` - List group iterations with filtering options
- `upload_markdown` - Upload a file to a GitLab project for use in markdown content
- `download_attachment` - Download an uploaded file from a GitLab project by secret and filename
- `list_events` - List all events for the currently authenticated user
- `get_project_events` - List all visible events for a specified project

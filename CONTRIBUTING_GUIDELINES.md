# Contributing Guidelines for Ovatify

Welcome to the Ovatify project! This document provides a detailed guide on how to contribute to the project using Git and GitHub. Our workflow is designed to maintain a clean, linear history using branching and rebasing, avoiding merge commits in our project history.

## Setting Up Your Development Environment

1. **Clone the Repository:**
   To start, clone the repository to your local machine:

   ```bash
   git clone https://github.com/enesonus/ovatify-backend.git
   ```

2. **Create a New Branch:**
   For every new feature or bugfix, create a new branch with your task number (e.g. OVTF-1,OVTF-96):

   ```bash
   git checkout -b OVTF-TaskNum
   ```

## Working on Your Feature

1. **Committing Changes:**
   After you are done with the task you can send it to your branch with:

   ```bash
   git add .
   git commit -m "Add a concise and informative commit message"
   ```

2. **Fetching Latest Main Branch:**
   Regularly fetch the latest changes from the main branch:

   ```bash
   git fetch origin main
   ```

3. **Rebasing onto Main:**
   Keep your feature branch updated by rebasing onto the main branch:

   ```bash
   git rebase origin/main
   ```

   If conflicts arise, resolve them (VS Code has a built in Merge editor for this), then continue rebasing:

   ```bash
   git rebase --continue
   ```

## Preparing to Merge

1. **Squashing Commits:**
   Before merging, squash your commits into a single commit for a cleaner history:

   ```bash
   git rebase -i <SHA of the latest commit before your commit>
   ```

   In the text editor, replace `pick` with `squash` (or `s`) beside all commits you want to squash.

2. **Writing Good Commit Messages:**
   - The first line should be a short summary of the changes, in the present tense.
   - Leave a blank line after the summary.
   - (Optional) Provide a detailed description of the changes on the following lines, wrapping the text at 72 characters.

   Example:

   ```bash
   OVTF-37 Implement user authentication

   Add user authentication using the XYZ library. It includes basic
   sign-up, sign-in, and sign-out features along with password encryption
   and session management.
   ```

## Submitting a Pull Request (PR)

1. **Push Your Branch:**
   Push your branch to GitHub named with the task number (e.g. OVTF-1, OVTF-98):

   ```bash
   git push -u origin OVTF-TaskNum
   ```

2. **Create a Pull Request:**
   - Go to the repository on GitHub.
   - Click on "Pull Request" and then "New Pull Request".
   - Select your branch and provide a concise, informative description of your changes.

3. **Code Review:**
   - Wait for a review from the team.
   - Make any requested changes and re-push your branch.

4. **Final Rebase:**
   Before your PR is merged, ensure your branch is rebased onto the latest main branch:

   ```bash
   git fetch origin main
   git rebase origin/main
   ```

5. **Merge and Clean-Up:**
   After the PR is approved, the repository maintainer will merge the branch.

## Additional Guidelines

- **Code Style and Standards:**
  Adhere to the coding style and standards agreed upon by the team.

- **Testing:**
  Ensure your code is well-tested and follows the project's testing guidelines. :))

- **Documentation:**
  Update or add documentation as needed.

By following these guidelines, we maintain a clean, understandable history and ensure a consistent workflow for everyone contributing to the project. Thanks for contributing to Ovatify! 🌟

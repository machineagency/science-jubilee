---
title: Code Contribution Guidelines
---

(code-contribution-guidelines)=
# Code Contribution Guidelines

## Issues

Most development starts with a GitHub Issue. See more about issues on the [Development page](https://machineagency.github.io/science-jubilee/development/index.html).

## Working on the `science-jubilee` Codebase

Once an issue has been discussed and assigned to you, you can begin implementing your changes! This involves 'forking' the repository (i.e., copying the repository to your personal GitHub account), making your changes, and then submitting a 'Pull Request' to add your functionality to the main repository. Here are the specific steps to follow to make sure this goes smoothly. We'll go into more detail on each of them here!

### Forking the Codebase

The first step to work on the codebase is to fork the repository. A 'fork' will copy the repository to your personal GitHub account so you can make and test your changes without affecting the base `science-jubilee` repo. Then, we can set up our workspace to make changes.

1. **Fork the repository.** From the main `science-jubilee`, you'll see a 'Fork' button just above the 'About' section. Click on this button and follow any pop-ups that appear.
2. **Clone your fork.** Once you create a fork, you can go to your fork's page on your own GitHub account. You can then clone (or download a copy) of your fork. To do so, click the green 'Code' button and copy the URL. Then, run the following command from the folder where you want to keep your repository:

```bash
git clone <url>
```

Replace `<url>` with the URL you just copied. After running this command, you should see all of the `science-jubilee` files on your computer.

3. **Add the upstream repository.** In git, 'upstream' refers to the original repository. To make sure we can sync up with the base repository, we have to explicitly set `science-jubilee` as the upstream repository. To do this, run the following command from the folder where you cloned the repository:

```bash
git remote add upstream https://github.com/machineagency/science-jubilee.git
```

For more details on configuring a remote repository for a fork, you can take a look at the [GitHub Documentation page](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-repository-for-a-fork).

4. **Make a new branch with a descriptive name.** It's useful to name your branch something descriptive, so that it is quickly clear what changes are being made. To do so, run the following command from the folder where you cloned the repository:

```bash
git checkout -b <descriptive_branch_name>
```

Replace `<descriptive_branch_name>` with your new name. For example, if you were adding a new camera tool, you might name your branch `new-camera-tool`.

5. **Install the requirements.** You can now install the requirements to use `science-jubilee`. Take a look at <project:#installation> for a reminder on how to do this.

<!-- the [Installation page](https://machineagency.github.io/science-jubilee/getting_started/installation.html#installation) -->

You should now be set up to make your changes!

### Git Workflow

*TODO: Add info on unit tests, once those are implemented*
As you make your changes, be sure to test often. This is to ensure that other code doesn't break when making your changes. Once unit tests are implemented, we'll add more details here.

As you're working on the codebase, you'll need to commit your changes to git. A 'commit' records the changes to a set of files. It can get confusing if you make too many changes in a single commit (e.g., it's hard to figure out where things are going wrong if something isn't working), or if you commit too many small changes (e.g., no need to make a commit after a change to a single line of code if you're going to make other related changes). A good rule of thumb is to commit whenever you've finished a task that can be summarized in a sentence-- use your best judgement!

A standard git workflow for committing changes is:

1. **Check your changes.** Run `git status` to see a list of your modified, added, and deleted files. Look through this list and make sure that it looks right. If there are files there that you didn't expect, you can double-check the changes by running `git diff`. If there are changes there that you did not intend, you should restore them back to their original state. You should not commit changes to any files which are not relevant to your specific pull

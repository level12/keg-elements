#!/bin/bash -e
#
# Author: Nick Zaccardi <nick.zaccardi@level12.io>
#
# This script is designed to help release packages to PyPI faster. It tries its
# best to walk you through all the steps to release a source packages and a
# binary wheel package.
#
# There are a few variables at the top that you should set:
#   - SRC_DIR
#   - REPO_URL for linking to individual commits
#
# The script does the following
#
# 1. Updates your version file ($SRC_DIR/version.py)
# 2. Adds any merge commits since the last tag to the changelog.rst file
# 3. Commits, tags and pushes those changes to the upstream repository
# 4. Creates, signs, and pushes the packages to PyPi

# VARIABLES
SRC_DIR=keg_elements
REPO_URL="https://github.com/level12/keg-elements"

# FUNCTIONS
confirm () {
    # call with a prompt string or use a default
    read -r -p "${1:-Are you sure?} [y/N]: " response
    case $response in
        [yY][eE][sS]|[yY])
            true
            ;;
        *)
            false
            ;;
    esac
}

check_for_auth() {
    FOUND_AUTH=false

    echo "Searching for credentials..."
    if [ -z $PYPI_USER ] || [ -z $PYPI_PASS ]; then
        echo "  PYPI_USER or PYPI_PASS not set looking for other auth method."
    else
        echo "  Found username and password in environment."
        FOUND_AUTH='env'
    fi


    if [ -z $FOUND_AUTH ] || [ ! -f "$HOME/.pypirc" ]; then
        echo "  Unable to find a ~/.pypirc file."
    else
        echo "  Found pypirc for authentication."
        FOUND_AUTH='file'
    fi

    if ! $FOUND_AUTH; then
        echo "ERROR: Unable to find an authentication mechanism"; exit 1;
    fi
    return FOUND_AUTH;
}

# ENVIRONMENT CHECKS;
test -z "$(git status --porcelain)" || { echo "Unclean head... aborting"; exit 1; }
HAS_SED=$(command -v sed 2>&1>/dev/null)
HAS_AWK=$(command -v awk 2>&1>/dev/null)
HAS_GPG=$(command -v gpg 2>&1>/dev/null)
PROJECT_NAME=$(python setup.py --name)
CURRENT_VERSION=$(python setup.py -V)

echo -n "Enter new version number (current $CURRENT_VERSION): "
read NEW_VERSION


if $HAS_SED && confirm "Update version file?"; then
    echo "VERSION = '$NEW_VERSION'" > $SRC_DIR/version.py
fi

CURRENT_GIT_TAG=$(git describe --tags --abbrev=0)
GIT_CHANGELOG=$(git log --merges --pretty=format:"* %s (%h_)" $CURRENT_GIT_TAG..HEAD)
GIT_CHANGELOG_LINKS=$(git log --merges --pretty=format:".. _%h: $REPO_URL/commit/%h" $CURRENT_GIT_TAG..HEAD)

echo -e "CHANGELOG UPDATES\n"
echo -e "$GIT_CHANGELOG\n"
echo "$GIT_CHANGELOG_LINKS\n"


if $HAS_AWK && confirm "Update changelog?"; then
    awk -v H="$NEW_VERSION - $(date +%Y-%m-%d)" \
        -v HB="------------------" \
        -v CL="$GIT_CHANGELOG" \
        -v CLL="$GIT_CHANGELOG_LINKS" \
        '/=========/{print;
                     print "";
                     print H;
                     print HB;
                     print "";
                     print CL;
                     print "";
                     print CLL;
                     print "";
                     next}1' \
        changelog.rst > tmp && mv tmp changelog.rst
fi


if confirm "Commit?"; then
    git add changelog.rst $SRC_DIR/version.py
    git commit --quiet -m "Version Bump $NEW_VERSION"
    GPG_TTY=$(tty) git tag --sign -m "Version Bump $NEW_VERSION" $NEW_VERSION

    if confirm "Push to Git remote?"; then
        echo -n "Which remote should I push to?"
        read UPSTREAM
        git push --tags $UPSTREAM master
    fi
fi

echo "Building package..."

rm -rf dist
pip --quiet install twine wheel
python setup.py --quiet sdist bdist_wheel

if $HAS_GPG && confirm "Sign files?"; then
    gpg --detach-sign -a "dist/$PROJECT_NAME-$(python setup.py -V).tar.gz"
    gpg --detach-sign -a "dist/$PROJECT_NAME-$(python setup.py -V)-py2.py3-none-any.whl"
fi

if confirm "Push to pypi?"; then
    twine upload dist/*
fi

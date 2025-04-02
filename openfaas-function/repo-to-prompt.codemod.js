/**
 * @param {vscode} vscode the entry to vscode plugin api
 * @param {vscode.Uri} selectedFile currently selected file in vscode explorer
 * @param {vscode.Uri[]} selectedFiles currently multi-selected files in vscode explorer
 */
async function run(vscode, selectedFile, selectedFiles) {
    console.log('You can debug the script with console.log')

    // Ask user for repository name
    const repoName = "openfaas-function";

    if (!repoName) {
        vscode.window.showErrorMessage('Repository name is required');
        return;
    }

    // remove useless file from selectedFiles
    selectedFiles = selectedFiles.filter(file => !file.path.endsWith('.env') && !file.path.endsWith('.lock') && !file.path.endsWith('LICENSE'));
    const lines = [];
    lines.push('\n<details>\n')
    for (const file of selectedFiles) {
        // Use regex to remove everything before the repo name
        const projectPath = file.path.replace(new RegExp(`^.*?(${repoName}/.*)$`), "$1");
        lines.push('<file path="' + projectPath + '">')
        lines.push(' ')
        lines.push('```')
        lines.push(new TextDecoder().decode(await vscode.workspace.fs.readFile(file)))
        lines.push('```')
        lines.push('</file>')
    }
    lines.push('\n</details>\n')
    await vscode.env.clipboard.writeText(lines.join('\n'))
    vscode.window.showInformationMessage('Copied to clipboard as Prompt XML.')
}
await run(vscode, selectedFile, selectedFiles);

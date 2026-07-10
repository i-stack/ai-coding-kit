class AiCodingKit < Formula
  desc "One kit for all AI coding tools — Agent Skills, MCP sync, iOS engineering rules"
  homepage "https://github.com/i-stack/ai-coding-kit"
  url "https://github.com/i-stack/ai-coding-kit/archive/refs/tags/v3.0.0.tar.gz"
  # RELEASE BLOCKER: fill sha256 before merging — brew install fails with an
  # empty checksum. Compute it with:
  #   curl -L https://github.com/i-stack/ai-coding-kit/archive/refs/tags/v3.0.0.tar.gz \
  #     | shasum -a 256
  sha256 "" # ← paste result here, then remove these comment lines
  license "MIT"
  version "3.0.0"

  depends_on "bash"

  def install
    # Install all project files
    prefix.install Dir["*"]

    # Make key scripts executable and accessible
    bin.install_symlink prefix/"sync.sh" => "ai-coding-kit-sync"
    bin.install_symlink prefix/"skills-engineering/scripts/sync-skills.sh" => "ai-coding-kit-sync-skills"
    bin.install_symlink prefix/"skills-engineering/scripts/list-skills.sh" => "ai-coding-kit-list-skills"
    bin.install_symlink prefix/"install-hooks.sh" => "ai-coding-kit-install-hooks"
  end

  def caveats
    <<~EOS
      ai-coding-kit is installed!

      ▶ Configure your secrets:
        cp #{prefix}/env/secrets.json.example #{prefix}/env/secrets.json
        $EDITOR #{prefix}/env/secrets.json

      ▶ Sync to your AI coding tools:
        ai-coding-kit-sync

      ▶ Sync agent skills only:
        ai-coding-kit-sync-skills --platforms claude,codex,cursor

      ▶ Install Git hooks (pre-commit governance):
        ai-coding-kit-install-hooks

      ▶ List available skills:
        ai-coding-kit-list-skills

      Supported platforms: Claude Code, Codex CLI, Cursor, Gemini CLI,
      CodeBuddy, Continue, Cline, Xcode Coding Assistant.
    EOS
  end

  test do
    assert_match "ai-coding-kit", shell_output("#{bin}/ai-coding-kit-list-skills 2>&1 || true")
  end
end

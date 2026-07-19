	// >>> mlbo-patch (local) — 멀티벤더 모드 전환 슬래시 커맨드. gjc update 후 apply-mlbo.sh 재실행 >>>
	{
		name: "mlbo",
		description: "Switch multivendor mode (model profile) for this session",
		inlineHint: "<profile|off>",
		allowArgs: true,
		subcommands: [
			// ↓ 각자 환경의 프로필 이름·설명(각주)으로 수정해서 쓰라. handle 은 어떤 프로필 이름이든 받는다.
			{ name: "daily-adapted", description: "⭐ 평소 기본 — 본체 Opus:med · exec Terra · plan Sol · arch/critic Gemini(gateway) ●●○○○" },
			{ name: "coding-sprint-adapted", description: "🏎 구현 스프린트 — executor Opus:high 승격 ●●●○○" },
			{ name: "cyber-cop-adapted", description: "🚨 리뷰어 모드 — PR 리뷰·보안 감사, architect/critic 주연 ●●●○○" },
			{ name: "llm-council-adapted", description: "🏛 4계열 합의 — Anthropic/OpenAI/Google/DeepSeek 판정석 ●●●●○" },
			{ name: "eco-adapted", description: "💸 저단가 — Terra:med + DeepSeek Flash + Luna ●○○○○" },
			{ name: "off", description: "모드 해제 — 영구 기본 프로필로 복귀" },
		],
		handle: async (command, runtime) => {
			const requested = command.args.trim().split(/\s+/)[0] ?? "";
			const profiles = runtime.session.modelRegistry.getModelProfiles();
			if (!requested) {
				const roster = [...profiles.keys()].sort((a, b) => a.localeCompare(b)).join(", ");
				await runtime.output(
					["Usage: /mlbo <profile|off> — activate a model profile for this session.", `Available: ${roster}`].join(
						"\n",
					),
				);
				return commandConsumed();
			}
			const profileName =
				requested === "off" ? (runtime.settings.get("modelProfile.default") ?? "") : requested;
			if (!profileName) {
				await runtime.output("mlbo: no persisted default profile to restore — pick a profile explicitly.");
				return commandConsumed();
			}
			try {
				await activateModelProfile({
					session: runtime.session,
					modelRegistry: runtime.session.modelRegistry,
					settings: runtime.settings,
					profileName,
				});
				const active = profiles.get(profileName);
				const seats = active
					? Object.entries(active.modelMapping)
							.map(([role, sel]) => `  ${role.padEnd(9)} ${sel}`)
							.join("\n")
					: "";
				await runtime.output(
					`Mode activated: ${profileName}${requested === "off" ? " (persisted default restored)" : ""}\n${seats}`,
				);
				await runtime.notifyTitleChanged?.();
				await runtime.notifyConfigChanged?.();
				return commandConsumed();
			} catch (err) {
				return usage(`mlbo: ${errorMessage(err)}`, runtime);
			}
		},
		handleTui: async (command, runtime) => {
			const result = await BUILTIN_SLASH_COMMAND_LOOKUP.get("mlbo")?.handle?.(
				command,
				toSlashCommandRuntime(runtime),
			);
			runtime.ctx.statusLine.invalidate();
			runtime.ctx.updateEditorBorderColor();
			runtime.ctx.editor.setText("");
			runtime.ctx.ui.requestRender();
			return result;
		},
	},
	// <<< mlbo-patch <<<

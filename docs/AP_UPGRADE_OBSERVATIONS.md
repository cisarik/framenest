Ledger storage version: 1
Upgrade ledger: upgrade https://github.com/cisarik/ap.git
Activation snapshot: zero candidate observations at 17b7e085139e9bcbb0e4953d26aef9b6687d541c

Entry: consumer-declared-execution-and-capability-route-binding
Entry state: accepted
Entry authority: non-authorizing
Summary: Consumer-declared AP exec and project SSH/sudo gates were bypassed by ambient raw Cursor Worker routes.
Evidence class: worker-observed
Observed against: 5abb2adfcd1d5f3391df9c3044b4b81ac1aac923
Last revalidated against: 7ef45da756ed3cc14808e89bf25d0a9f9aba5d26
Implementation task grant: none
Implementation status: not-started
Disposition evidence: 7ef45da756ed3cc14808e89bf25d0a9f9aba5d26 (.ap/ap; .ap/docs/adr/0012-baseline-bound-project-execution.md; .ap/docs/adr/0018-consumer-declared-execution-route-binding.md)
Promotion target: none
Closure action: retain-active
Historical evidence: none
Provenance destroyed: no

Entry: darwin-bsd-awk-project-argv-counting
Entry state: implemented
Entry authority: non-authorizing
Summary: Project key counting used an awk NUL record separator that BSD/macOS awk does not implement, so ap project check and exec failed closed on macOS with a false newline error; AP now counts with a portable tr/wc pipeline.
Evidence class: worker-observed
Observed against: 7478ddb07d2c3911f79e1aa1441f0115a31c45d8
Last revalidated against: 73e20ef80b88700d5fcbc397cd8edd4fc425869f
Implementation task grant: none
Implementation status: implemented with 73e20ef80b88700d5fcbc397cd8edd4fc425869f
Disposition evidence: 73e20ef80b88700d5fcbc397cd8edd4fc425869f (.ap/ap; macOS 26.6.1 /usr/bin/awk reproduction)
Promotion target: none
Closure action: remove-from-active-ledger
Historical evidence: 73e20ef80b88700d5fcbc397cd8edd4fc425869f
Provenance destroyed: no

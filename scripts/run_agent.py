"""Run the Northstar HR agent and optionally display its trace."""



from __future__ import annotations



import argparse

import asyncio

import json



from src.agent.orchestrator import run_agent





def build_parser() -> argparse.ArgumentParser:

    """Create command-line arguments for an agent request."""



    parser = argparse.ArgumentParser(

        description="Run the Northstar HR agent.",

    )



    parser.add_argument(

        "question",

        nargs="+",

        help="The HR question or request.",

    )

    parser.add_argument("--work-email")

    parser.add_argument("--full-name")

    parser.add_argument("--employee-id")

    parser.add_argument("--start-date")

    parser.add_argument("--end-date")

    parser.add_argument("--requested-days", type=float)

    parser.add_argument(

        "--confirm",

        action="store_true",

        help="Explicitly confirm a confirmation-gated mock action.",

    )

    parser.add_argument(

        "--show-trace",

        action="store_true",

        help="Display the concise operational trace as JSON.",

    )



    return parser





async def main() -> None:

    """Run the requested agent workflow."""



    args = build_parser().parse_args()

    question = " ".join(args.question)



    result = await run_agent(

        question,

        work_email=args.work_email,

        full_name=args.full_name,

        employee_id=args.employee_id,

        start_date=args.start_date,

        end_date=args.end_date,

        requested_days=args.requested_days,

        confirmed=args.confirm,

    )



    print("\nAnswer\n")

    print(result.answer)



    print("\nAnswer basis\n")

    for item in result.answer_basis:

        print(f"- {item}")



    print(f"\nRequires confirmation: {result.requires_confirmation}")

    print(f"Escalation required: {result.escalation_required}")



    if args.show_trace:

        print("\nOperational trace\n")

        print(

            json.dumps(

                [event.to_dict() for event in result.trace],

                indent=2,

            )

        )





if __name__ == "__main__":

    asyncio.run(main())

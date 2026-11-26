cwlVersion: v1.0
class: Workflow
id: echo
inputs:
  message:
    type: string
  count:
    type: int?
outputs:
  out:
    type: File
    outputSource: echo_step/out
steps:
  echo_step:
    run:
      class: CommandLineTool
      baseCommand: echo
      inputs:
        text:
          type: string
          inputBinding:
            position: 1
      outputs:
        out:
          type: stdout
    in:
      text: message
    out:
      - out

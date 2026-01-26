import React, { useState, forwardRef } from "react";
import { observer } from "mobx-react";
import { TextArea } from "../../common/TextArea/TextArea";
import { Button } from "@humansignal/ui";
import { getRoot } from "mobx-state-tree";

const STATUS_TAGS = [
  {
    label: "审核通过",
    value: 1,
    color: "green",
  },
  {
    label: "需重标",
    value: 2,
    color: "red",
  },
  {
    label: "数据抛弃",
    value: 3,
    color: "orange",
  },
];

const CheckStatusFormComponent = observer(
  forwardRef(({ store }, ref) => {
    console.log("lm--------CheckStatusFormComponent-store", store);

    const [description, setDescription] = useState(store.task?.audit_reason);
    const [singleSelected, setSingleSelected] = useState(
      store.task?.audit_status,
    );

    const handleSelectedTag = (item) => {
      setSingleSelected(item.value);
    };

    const handleSave = async (event) => {
      // 关闭下拉菜单
      if (ref?.current && typeof ref.current.close === "function") {
        ref.current.close();
      }

      try {
        // 获取当前任务ID
        const currentTaskId =
          store.taskId || store.task?.id || store.selected?.id;

        if (!currentTaskId) {
          console.error("Current task ID is not available");
          return;
        }

        // 准备更新数据
        const updateData = {
          audit_status: singleSelected,
          audit_reason: description,
        };

        console.log(
          "lm------handleSave-store",
          store,
          currentTaskId,
          updateData,
        );

        const apiCallResult = await store.updateTask(currentTaskId, updateData);
        window.location.reload();

        console.log("lm------handleSave-success", singleSelected, description);
      } catch (error) {
        console.error("Failed to update task:", error);
      }
    };

    return (
      <div className="w-[360px]">
        <div className="flex justify-between items-center mb-[12px] p-[12px] border-b border-gray-200">
          <div>审核标注</div>
          <Button
            disabled={!singleSelected}
            size="small"
            className="w-[100px]"
            onClick={handleSave}
          >
            保存
          </Button>
        </div>
        <div className="p-[12px]">
          <div className="flex justify-between items-center">
            {STATUS_TAGS.map((item) => (
              <div
                className="bg-[#F5F5F5] w-[100px] rounded-[4px] leading-[36px] font-bold text-center mr-[8px] cursor-pointer"
                key={item.value}
                style={
                  item.value === singleSelected
                    ? { background: item.color, color: "#fff" }
                    : {}
                }
                onClick={() => handleSelectedTag(item)}
              >
                {item.label}
              </div>
            ))}
          </div>
          <TextArea
            name="description"
            id="project_description"
            placeholder="Optional description of your project"
            rows="4"
            style={{ minHeight: 100, padding: "12px" }}
            value={description}
            onChange={(val) => setDescription(val)}
            className="project-description w-full mt-[12px] border border-gray-200"
          />
        </div>
      </div>
    );
  }),
);

export default CheckStatusFormComponent;

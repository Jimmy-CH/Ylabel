import { isDefined } from "../../utils/utils";

const formatNumber = (num) => {
  const number = Number(num);

  if (num % 1 === 0) {
    return number;
  }
  return number.toFixed(3);
};

// 审核状态映射函数
const formatAuditStatus = (value, column) => {
  // 检查是否是审核状态列
  if (column.column.original?.id?.split(":")[1] === "audit_status") {
    // 将数字转换为对应的中文状态
    switch (Number(value)) {
      case 0:
        return "待审核";
      case 1:
        return "审核通过";
      case 2:
        return "需重标";
      case 3:
        return "数据抛弃";
      default:
        return `未知状态(${value})`;
    }
  }

  // 对于其他数字列，使用默认格式化
  return formatNumber(value);
};

export const NumberCell = (column) => {
  console.log("lm-------NumberCell-column", column);
  if (!isDefined(column.value)) {
    return "";
  }

  return formatAuditStatus(column.value, column);
};
// NumberCell.userSelectable = false;

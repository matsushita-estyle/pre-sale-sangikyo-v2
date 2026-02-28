'use client'

import { useQuery } from '@tanstack/react-query'
import { MainLayout } from '@/components/layout/MainLayout'
import { getUsers, getCustomers, getDeals } from '@/lib/api'

export default function DataPage() {
  const {
    data: users = [],
    isLoading: usersLoading,
    error: usersError,
  } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  })

  const {
    data: customers = [],
    isLoading: customersLoading,
    error: customersError,
  } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers,
  })

  const {
    data: deals = [],
    isLoading: dealsLoading,
    error: dealsError,
  } = useQuery({
    queryKey: ['deals'],
    queryFn: getDeals,
  })

  const isLoading = usersLoading || customersLoading || dealsLoading
  const error = usersError || customersError || dealsError

  if (isLoading) {
    return (
      <MainLayout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-lg">Loading...</div>
        </div>
      </MainLayout>
    )
  }

  if (error) {
    return (
      <MainLayout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-red-500">
            Error: {error instanceof Error ? error.message : 'Unknown error'}
          </div>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Cosmos DB Data Verification</h1>

        {/* Users Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">Users ({users.length})</h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Department
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.user_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {user.user_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {user.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.department || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.role || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Customers Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">
            Customers ({customers.length})
          </h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Industry
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contact Person
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Phone
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {customers.map((customer) => (
                  <tr key={customer.customer_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {customer.customer_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {customer.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {customer.industry || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {customer.contact_person || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {customer.email || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {customer.phone || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Deals Section */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">
            Deals ({deals.length})
          </h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    顧客
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    営業担当
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ステージ
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    サービス種別
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    金額
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    最終接触日
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {deals.map((deal) => (
                  <tr key={deal.deal_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {deal.deal_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {deal.customer_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {deal.sales_user_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          deal.deal_stage === '受注'
                            ? 'bg-green-100 text-green-800'
                            : deal.deal_stage === '失注'
                            ? 'bg-red-100 text-red-800'
                            : deal.deal_stage === '商談'
                            ? 'bg-blue-100 text-blue-800'
                            : deal.deal_stage === '提案'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {deal.deal_stage}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {deal.service_type || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {deal.deal_amount
                        ? `¥${deal.deal_amount.toLocaleString()}`
                        : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {deal.last_contact_date || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        </div>
      </div>
    </MainLayout>
  )
}
